import os
import pandas as pd
import re
from datetime import datetime
from tqdm import tqdm
import psycopg2

def extract_837_data(file_path,edi_text=None,file_date=None,filename=None):
    if not edi_text:
        filename = os.path.basename(file_path)
        match = re.search(r'\d{8}', filename)
        if 'HCP' in filename:
            file_type = 'P'
        elif 'HCI' in filename:
            file_type = 'I'
        if match:
            date_str = match.group()
            print("Filename:", filename)
            print("Extracted date:", date_str)
        else:
            print("Date not found in filename")
        print(file_path,'file_path')
        with open(file_path, "rb") as f:
            edi_text = f.read().decode("utf-8", errors="ignore")
    segments = edi_text.strip().split('~')
    lab = 0
    im_rows = []
    STAT_NAME = ''
    try:
        formatted_date = datetime.strptime(date_str, "%m%d%Y").strftime("%y%m%d")
    except:
        formatted_date = file_date
    print("this is formatted date",formatted_date)
    inc_val = '0003'
    sequence = -2
    file_type = filename[2]
    for segment in segments:
        sequence += 1
        if not segment.strip():
            continue
        parts = segment.split('*')
        seg_name = parts[0]
        if seg_name == 'GS':
            STAT_NAME = parts[2]
        if seg_name == 'ST':
            last_part = parts[-1]
            im_rows.append({"BICCBT":f"{formatted_date}{inc_val}","BICCSQ":sequence,"BIPROC":'Y',"BITRID":f"837_5{file_type}","BIIDFR":"PEH","BIDAT1":f"{str(sequence+1).zfill(8)}{STAT_NAME}*{last_part}"})
            continue
        segment_body = '*'.join(parts[1:])
        if seg_name !='ISA' and seg_name != 'GS':
            im_rows.append({"BICCBT":f"{formatted_date}{inc_val}","BICCSQ":sequence,"BIPROC":'Y',"BITRID":f"837_5{file_type}","BIIDFR":seg_name,"BIDAT1":f"{str(sequence+1).zfill(8)}{STAT_NAME}*{segment_body}"})
    
    return im_rows,file_type,filename,date_str


def smart_split(s):
    return s.split('*')


def get_element(segment_str, element, flag,q):
    parts = smart_split(segment_str)
    if '+' in element:

        elements = [e.strip() for e in element.split('+')]
        values = []

        for el in elements:

            if ':' in el:  
                base, sub = el.split(':')
                idx = int(base[-2:])
                if idx < len(parts):
                    sub_parts = parts[idx].split(':')
                    sub_idx = int(sub) - 1
                    if sub_idx < len(sub_parts):
                        values.append(sub_parts[sub_idx])

            else:
                idx = int(el[-2:])
                if idx < len(parts):
                    values.append(parts[idx])

        return " ".join(values), element,''

    if ':' in element:
        base, sub = element.split(':')
        idx = int(base[-2:])
        if idx < len(parts):
            sub_parts = parts[idx].split(':')
            sub_idx = int(sub)
            if sub_idx < len(sub_parts):
                return sub_parts[sub_idx], element,''
            else:
                return '',element,''

    try:
        index = int(element[-2:])
    except:
        index = int(element.split(":")[1])
    try:
        if element == "HCP06" and parts[index] == '':
            index = 14
    except:
        pass
    
    if index < len(parts):
        d = ''
        e = ''
        field = ''
        if 'REF' in element:
            if parts[1] == q:
                d = parts[index]
                e = element
        elif 'PRV' in element:
            if q == 'PE' and parts[1] == q:
                d = parts[index]
                e = element
            elif q == 'BI' and parts[1] == q:
                d = parts[index]
                e = element
        elif 'CAS' in element and q == 'PR':
            if parts[2] == '3':
                d = parts[index]
                e = element
                field = 'BHOICP'
            elif parts[2] == '1':
                d = parts[index]
                e = element
                field = 'BHOIDE'
            elif parts[2] == '2':
                d = parts[index]
                e = element
                field = 'BHOICO'
        elif 'DTP' in element and q == '435':
            if parts[1] == '435':
                d = parts[index]
                e = element
            else:
                d = '0'
                e = element
        else:
            d = parts[index]
            e = element

        return d, index,field
    
    return "", element,""


def parse_df(df, mappings):
    parsed_rows = []
    segment_data_sub = {}
    segment_data_dep = {}
    flag = 0
    is_dependent_section = False
    current_entity = None   

    for _, row in df.iterrows():

        seg = str(row["BIIDFR"]).strip()
        segment_str = str(row["BIDAT1"]).strip()

        parts = smart_split(segment_str)

        if seg == "HL":

            if len(parts) > 3:
                hl_code = parts[3]

                if hl_code == "22":
                    is_dependent_section = False

                elif hl_code == "23":
                    is_dependent_section = True

            continue

        current_data = segment_data_dep if is_dependent_section else segment_data_sub

        qualifier = parts[1] if len(parts) > 1 else ""
        
        if seg == "NM1":

            nm1_qual = parts[1] if len(parts) > 1 else ""
           
            entity_map = {
                "41": "Submitter",
                "40": "Receiver",
                "85": "Billing",
                "87": "PayTo",
                "IL": "Subscriber",
                "PR": "Payer",
                "QC": "Dependent",
                "77": "Service Location",
                "82": "Attending Physician"
            }
            if nm1_qual == 'IL' and str(parts[2]) == '2': 
                current_entity = ''
            else:
                current_entity = entity_map.get(nm1_qual)
        if seg == 'CLM':
            qualifier = ''
            current_entity = ''
        
        if seg == 'SBR':
            qualifier = ''

        rules = [
            m for m in mappings
            if m["segment"] == seg and (
                (m.get("qualifier") == qualifier) or
                (m.get("entity") == current_entity) or
                (m.get("qualifier","") == "" and "entity" not in m)
            )
        ]

        
        flag+=1
        for rule in rules:
            element = rule["element"]
            field = rule["field"]
            q = rule['qualifier']
            value, ele, f = get_element(segment_str, element, flag,q)
            if value:
                if field == 'BHMLNM' and value == 'REQ FOR ANTHEM SVD':
                    pass
                elif field == 'BHPNAM' and value == 'REQ FOR ANTHEM SVD':
                    pass
                elif field == 'BHDLNM' and value == 'REQ FOR ANTHEM SVD':
                    pass
                elif field == 'BHSNAM' and value == 'REQ FOR ANTHEM SVD':
                    pass
                elif field == 'BHMLNM' and value == 'ANTHEM REJECT CLAIM':
                    pass
                elif field == 'BHPNAM' and value == 'ANTHEM REJECT CLAIM':
                    pass
                elif field == 'BHDLNM' and value == 'ANTHEM REJECT CLAIM':
                    pass
                elif field == 'BHSNAM' and value == 'ANTHEM REJECT CLAIM':
                    pass
                elif field == 'BHDOCN':
                    existing_value = str(current_data.get(field, '')).strip()
                    if existing_value == '':
                        current_data[field] = value
                elif field == 'BHOICP' and f == 'BHOICP':
                    current_data[field] = value
                elif field == 'BHOICO' and f == 'BHOICO':
                    current_data[field] = value
                elif field == 'BHNPA1':
                    existing_value = str(current_data.get(field, '')).strip()
                    if existing_value == '':
                        current_data[field] = value
                elif field == 'BHPHNM':
                    existing_value = str(current_data.get(field, '')).strip()
                    if existing_value == '':
                        current_data[field] = value
                elif field == 'BHSAD1':
                    existing_value = str(current_data.get(field, '')).strip()
                    if existing_value == '':
                        current_data[field] = value
                elif field == 'BHSCTY':
                    existing_value = str(current_data.get(field, '')).strip()
                    if existing_value == '':
                        current_data[field] = value
                elif field == 'BHCAMT':
                    existing_value = str(current_data.get(field, '')).strip()
                    if existing_value == '':
                        current_data[field] = value
                elif field == 'BHCFID':
                    existing_value = str(current_data.get(field, '')).strip()
                    if existing_value == '':
                        current_data[field] = value
                elif field == 'BHNPA2':
                    existing_value = str(current_data.get(field, '')).strip()
                    if existing_value == '':
                        current_data[field] = value
                elif field == 'BHOIDE' and f == 'BHOIDE':
                    existing_value = str(current_data.get(field, '')).strip()
                    if existing_value == '':
                        current_data[field] = value
                elif field == 'BHSNPINS':
                    existing_value = str(current_data.get('BHSNPINS', '')).strip()
                    if len(existing_value) < 8:
                        if len(str(value).strip()) >= 8:
                            current_data['BHSNPINS'] = value
                elif field == 'BHNPI':
                    existing_value = str(current_data.get('BHNPI', '')).strip()
                    if len(existing_value) < 8:
                        if len(str(value).strip()) >= 8:
                            current_data['BHNPI'] = value
                            
                else:
                    if field == 'BHOICP':
                        pass
                    elif field =='BHOIDE':
                        pass
                    else:
                        current_data[field] = value
        if seg == "SE":
            parsed_rows.append(segment_data_sub)

            if segment_data_dep:
                parsed_rows.append(segment_data_dep)

            segment_data_sub = {}
            segment_data_dep = {}

            is_dependent_section = False
            current_entity = None

    return pd.DataFrame(parsed_rows)


def process_df(df,filetype,im_df,filename=None):
    print('processing started')
    df['BHPAYC'] = df['BHPPOI'].apply(
        lambda x: '1' if str(x).strip() in ['IN-Y', 'IN-N','ON-Y']
        else '2' if str(x).strip() in ['ON-N']
        else ''
    )
    def map_bhppoi(x):
        x = str(x).strip()
        if x in ['IN-Y', 'IN-N', 'Y','1']:
            return '1'
        elif x in ['ON-Y', 'N', 'ON-N']:
            return '2'
        return x
    df["BHPPOI"] = df["BHPPOI"].apply(map_bhppoi)
    df['BHPARN'] = df['BHPAYC'].apply(
        lambda x: 'P' if str(x).strip() == '1'
        else 'N' if str(x).strip() == '2'
        else ''
    )
    df['BHRCVI'] = 'OOE01'
    df['BHAMDG'] = df['BHDIO1']

    if filetype == 'P':
        try:
            df['BHSNPI'] = df.apply(
            lambda row: row['BHSID']
            if pd.notna(row['BHSID']) and str(row['BHSID']).strip().lower() != 'nan' and str(row['BHSID']).strip() != ''
            else row['BHPHID'],
            axis=1
            )
        except:
            try:
                df['BHSNPI'] = df['BHSID']
            except:
                df['BHSNPI'] = ''
    try:
        df.drop(columns=['BHSID'],inplace=True)
    except:
        pass

    if 'BHSNPI' in df.columns:
        mask = (
        df["BHSNPI"].isna()
        |
        (df["BHSNPI"].astype(str).str.strip() == "")
        )

        df.loc[mask, "BHSNPI"] = df.loc[mask, "BHSNPIDN"]

    df['BHPAD1'] = df.apply(lambda row: row['BLPAD1'] if pd.isna(row['BHPAD1']) or str(row['BHPAD1']).strip().lower() in ['', 'nan'] else row['BHPAD1'], axis=1)
    df['BHPCTY'] = df.apply(lambda row: row['BLPCTY'] if pd.isna(row['BHPCTY']) or str(row['BHPCTY']).strip().lower() in ['', 'nan'] else row['BHPCTY'], axis=1)
    df['BHPST'] = df.apply(lambda row: row['BLPST'] if pd.isna(row['BHPST']) or str(row['BHPST']).strip().lower() in ['', 'nan'] else row['BHPST'], axis=1)
    df['BHPZIP'] = df.apply(lambda row: row['BLPZIP'] if pd.isna(row['BHPZIP']) or str(row['BHPZIP']).strip().lower() in ['', 'nan'] else row['BHPZIP'], axis=1)
    df.drop(columns=['BLPAD1', 'BLPCTY', 'BLPST', 'BLPZIP'], inplace=True, errors='ignore')
    df.loc[df["BHPPOI"] == '1', "BHCNCD"] = 101
    df.loc[df["BHPPOI"] == '2', "BHCNCD"] = 102
    df.loc[df["BHPPOI"] == '3', "BHCNCD"] = 103
    df.to_excel('check_dob.xlsx')
    def convert_date_col(val):
        if pd.isna(val):
            return val

        val = str(val).strip()
        try:
            if float(val).is_integer():
                val = str(int(float(val)))
        except:
            pass

        if len(val) == 8 and val.isdigit():

            yyyy = val[:4]
            mm = str(int(val[4:6]))
            dd = str(int(val[6:8]))

            return mm + dd + yyyy

        return val

    source_cols = ["BHDIO1", "BHDIO2", "BHDIO3", "BHDIO4", "BHDIO5", "BHDIO6", "BHDIO7", "BHDIO8"]
    target_cols = ["BHDIO1", "BHDIO2", "BHDIO3", "BHDIO4", "BHDIO5"]
    try:
        def extract_ab_codes(row):

                values = []
                for col in source_cols:

                    val = row[col]

                    if pd.isna(val):
                        continue

                    val = str(val).strip()

                    if ":" not in val:
                        continue

                    prefix, code = val.split(":", 1)

                    if prefix in ["ABK", "ABF"]:
                        values.append(code)

                result = values[:5]

                while len(result) < 5:
                    result.append("")

                return pd.Series(result, index=target_cols)
        df[target_cols] = df.apply(extract_ab_codes, axis=1)
        df.drop(columns=["BHDIO6", "BHDIO7", "BHDIO8"], inplace=True, errors="ignore")
    except:
        pass
    
    try:
        cols = ['BHDIO1', 'BHDIO2', 'BHDIO3', 'BHDIO4', 'BHDIO5']
        for col in cols:
            df[col] = df[col].apply(
                lambda x: '' if pd.notna(x) and len(str(x).strip()) < 3 else x
            )
    except:
        pass
    df['BHDOCN'] = df['BHDOCN'].apply(
    lambda x: str(x).replace('WGS20', '') if pd.notna(x) and str(x).endswith('WGS20') else x
    )
    df['BHADJR'] = df['BHADJR'].astype(str).str.replace('-', '', regex=False)
    df['BHDOCN'] = (
        df['BHDOCN'].astype(str)
        +
        df['BHADJR'].astype(str).str[-3:]
    )
    df['BHADJR'] = df['BHADJR'].apply(
        lambda x: '' if str(x).endswith('000') else x
    )
    df['BHADJR'] = df['BHADJR'].astype(str).str[-3:]
    # df.to_excel(r"bhtaxo_check.xlsx")
    if filetype == 'P':
        try:
            df['BHTAXO'] = df.apply(
            lambda row: row['BHTAXO2']
            if pd.isna(row['BHTAXO']) or str(row['BHTAXO']).strip() == ''
            else row['BHTAXO'],
            axis=1
            )
            df.drop(columns = ['BHTAXO2'],inplace =True)
        except:
            df['BHTAXO'] = df['BHTAXO2']
    else:
        df.rename(columns={'BHTAXO2':'BHTAXO'},inplace=True)
    df.to_excel(r"bhtaxo_check_after_map.xlsx")
    if filetype == 'I':
        df.rename(columns={'BHSNPINS':'BHSNPI'},inplace=True)
    else:
        if 'BHSNPINS' in df.columns:
            df.drop(columns=['BHSNPINS'],inplace=True)

    try:
        df['BHOIAL'] = (
        pd.to_numeric(df['BHOICP'], errors='coerce').fillna(0)
        +
        pd.to_numeric(df['BHOPPA'], errors='coerce').fillna(0)
        )
    except:
        pass

    
    df.to_excel('check_bhdmrert_prof_NEWi.xlsx')
    df['mem_dob'] = df['BHMBDT']
    try:
        df['dep_dob'] = df['BHDBDT']
    except:
        df['dep_dob'] = df['BHMBDT']
    for i, row in df.iterrows():
        bhdmre_value = str(row["BHDMRE"]).strip()
        clm_df = im_df[im_df["BIIDFR"].str.startswith("CLM", na=False)]
        match_rows = clm_df[clm_df["BIIDFR"].str.contains(bhdmre_value, na=False)]

        if not match_rows.empty:
            matched_index = match_rows.index[0]    
            df.at[i, "BHSQCL"] = matched_index
        else:
            df.at[i, "BHSQCL"] = ""
    try:
        df.loc[df["BHDFNM"].isna() | (df["BHDFNM"] == ""), "BHDFNM"] = df["BHMFNM"]
        df.loc[df["BHDLNM"].isna() | (df["BHDLNM"] == ""), "BHDLNM"] = df["BHMLNM"]
    except:
        df['BHDFNM'] = df['BHMFNM']
        df['BHDLNM'] = df['BHMLNM']
        df['BHDBDT'] = df['BHMBDT']
    try:
        conn = conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="claims_db",
            user="onesmarter",
            password="kriskross$1"
        )
        print("Connected to Postgress database.")
        cursor = conn.cursor()
    except Exception as e:
        print("DB2 connection error:", e)
        exit()
    unique_member_ids = df['BHORGN'].dropna().unique()
    denied_claims = []
    manual_lookup_claims = []
    jh = 0
    for member_id in tqdm(unique_member_ids, desc="Processing Member IDs"):
        jh += 1
        df_rows = df[df['BHORGN'] == member_id]
        mem_dob = df_rows['mem_dob']
        dep_dob = df_rows['dep_dob']
        if True:
            results = None
            search_columns = ['TEALTI', 'TEHCID', 'TEHMID']
            query_template = """
                SELECT
                    "TECLNT",
                    "TESEQ",
                    "TESSN",
                    "TEDSSN",
                    "TENAME",
                    "TEDOB"
                FROM ediemp
                WHERE "{column}" = %s
            """

            cursor = conn.cursor()
            found = False
            for column in search_columns:
                query = query_template.format(column=column)
                cursor.execute(query, (member_id,))
                results = cursor.fetchall()
                if results:
                    found = True
                    break
            if not found:
                denied_claims.append(df_rows.copy())

            
            if results:
                matched_indexes = set()
                date_series = df_rows.apply(
                    lambda row: (
                        row["dep_dob"]
                        if pd.notna(row["dep_dob"]) and str(row["dep_dob"]).strip() != ""
                        else row["mem_dob"]
                    ),
                    axis=1
                )
                for result_row in results:
                    teclnt, teseq, tessn, tedssn, tename, tedob = result_row
                    if not tename or '*' not in tename:
                        continue

                    last_name, first_name = tename.split('*', 1)
                    temp_name = str(tename).strip()
                    tedob_str = str(int(tedob))
                    t_las = last_name.strip().upper().replace(" ", "")
                    name_matched_rows = df_rows[
                        (
                            df_rows['BHDFNM']
                            .astype(str)
                            .str.strip()
                            .str.upper()
                            .str.split()
                            .str[0]
                            ==
                            first_name.strip().upper().split()[0]
                        )
                        &
                        (
                            df_rows['BHDLNM']
                            .astype(str)
                            .str.strip()
                            .str.upper()
                            .str.replace(" ", "", regex=False)
                            ==
                            last_name.strip().upper().replace(" ", "")
                        )
                    ]
                    if name_matched_rows.empty:
                        continue
                    
                    print(f"this is {date_series}____{tedob_str}")
                    matched_rows = name_matched_rows[
                        date_series.loc[name_matched_rows.index] == tedob_str
                    ].copy()

                    if not matched_rows.empty:
                        matched_indexes.update(matched_rows.index)
                        for df_index in matched_rows.index:
                            df.at[df_index, 'TECLNT'] = teclnt
                            df.at[df_index, 'TESEQ'] = teseq
                            df.at[df_index, 'TESSN'] = tessn
                            df.at[df_index, 'TEDSSN'] = tedssn
                            # df.at[df_index,'BHMVRF'] = 'Y'

                unmatched_rows = df_rows[
                    ~df_rows.index.isin(matched_indexes)
                ]
                if not unmatched_rows.empty:
                    manual_lookup_claims.append(unmatched_rows.copy())

            else:
                print(f"No results found for member ID {member_id}")
            


    df['BHCLNT'] = df['TECLNT']
    df['BHPSEQ'] = df['TESEQ']
    df['BHMEMN'] = df['TESSN']
    df.drop(columns=['TECLNT','TESEQ','TESSN'],inplace=True)
    df.to_excel('after_samsung_new.xlsx')
    ins_mapping = {
    '1':'01',
    '3':'19',
    '2':'19',
    '9':'19'
    }
    for i, row in df.iterrows():
        dpssn = row["BHMEMN"]
        dpseq = str(row["BHPSEQ"]).strip()
        if dpseq == 'nan':
            dpseq = ''
        if dpssn and dpseq:
            dpssn = str(row["BHMEMN"]).strip()
            dpseq = int(row["BHPSEQ"])


            if dpseq == 0:
                df.at[i, "BHRLTN"] = "1"
                df.at[i, "BHDREL"] = "18"
                continue

            cursor.execute(
                """
                SELECT "DPRLTN"
                FROM depnp
                WHERE "DPSSN" = %s
                AND "DPSEQ" = %s
                """,
                (dpssn, dpseq)
            )
            result = cursor.fetchone()

            if result:
                dprltn = str(result[0]).strip()
                if dprltn =='1':
                    df.at[i, "BHRLTN"] = '2'
                else:
                    df.at[i, "BHRLTN"] = '3'
                df.at[i, "BHDREL"] = ins_mapping.get(dprltn, None)
            else:
                df.at[i, "BHRLTN"] = None
                df.at[i, "BHDREL"] = None
    df['BHDEPN'] = df['BHPSEQ']
    df['BHPAD1'].fillna('',inplace=True)
    df['BHPCTY'].fillna('',inplace=True)
    df['BHPST'].fillna('',inplace=True)
    df['BHLDWK'] = ''
    df["BHCFID"] = df["BHCFID"].replace("", "CI")
    df["BHCFID"] = df["BHCFID"].fillna("CI")
    df["BHMBDT"] = df["BHMBDT"].apply(convert_date_col)
    df["BHDBDT"] = df["BHDBDT"].apply(convert_date_col)
    df.to_excel(r"before_bh.xlsx")
    deny_df = pd.concat(denied_claims, ignore_index=True) if denied_claims else pd.DataFrame()
    manual_lookup_df = pd.concat(manual_lookup_claims, ignore_index=True) if manual_lookup_claims else pd.DataFrame()
    provp_new = []
    for i, row in tqdm(df.iterrows(), total=len(df), desc="Processing BH data"):
        name = str(row["BHPNAM"]).replace(" ", "").strip()
        addr1 = str(row["BHPAD1"]).replace(" ", "").strip()
        city = str(row["BHPCTY"]).replace(" ", "").strip()
        state = str(row["BHPST"]).replace(" ", "").strip()
        zip_code = row['BHPZIP']
        if pd.notna(zip_code) and str(zip_code).strip().lower() != "nan":
            zip_code = str(int(float(zip_code)))
        else:
            zip_code = ""
        zip_code = zip_code[:5]
        prnum = str(row["BHTXID"]).strip()

        if not prnum or prnum =='nan':
            continue

        name  = "%" + name.replace(" ", "").replace("-", "").upper() + "%"
        addr1 = "%" + addr1.replace(" ", "").replace("-", "").upper() + "%"
        city  = "%" + city.replace(" ", "").upper() + "%"

        sql = """
        SELECT
            MAX("PRSEQ"),
            MAX("PRBSEQ")
        FROM provp
        WHERE REPLACE(REPLACE(UPPER("PRPNAM"), ' ', ''), '-', '') LIKE %s
        AND REPLACE(REPLACE(UPPER("PRADR1"), ' ', ''), '-', '') LIKE %s
        AND REPLACE(UPPER("PRCITY"), ' ', '') LIKE %s
        AND "PRST" = %s
        AND "PRZIP5" = %s
        AND "PRNUM" = %s
        """

        cursor.execute(
            sql,
            (
                name,
                addr1,
                city,
                state,
                zip_code,
                str(prnum)
            )
        )
        result = cursor.fetchone()

        
        if not result[0]:
            provp_new.append(row)
        if result:
            df.at[i, "BHPSEQ"] = result[0]
            df.at[i,"BHPRVRF"] = 'Y'
            if result[1]:
                df.at[i, "BHPBSEQ"] = result[1]
            else:
                df.at[i, "BHPBSEQ"] = result[0]
        else:
            df.at[i, "BHPSEQ"] = None
            df.at[i, "BHPBSEQ"] = ''
            

    df['BHDCNT'] = df['BHDOCN']
    try:
        df['BHREFC'] = df['BHGRNM'].astype(str).str.split('-')[0]
    except:
        try:
            df['BHREFC'] = df['BHGRNM']
        except:
            df['BHREFC'] = ''
    df['BHTXSN'] = 'T'
    try:
        df['BHCLTP'] = filetype
    except:
        pass


    df["BHBFRD"] = df["BHBFRD"].str.split("-").str[0]
    df["BHBTOD"] = df["BHBTOD"].str.split("-").str[1]
    df["BHPLSR"] = df["BHPLSR"].str.split(":").str[0]
    df["BHFREQ"] = df["BHFREQ"].str.split(":").str[2]
    prov_to_insert_df = pd.DataFrame([
    dict(x) if not isinstance(x, dict) else x
    for x in provp_new
    ])
    prov_to_insert_df.to_excel('provider_to_insert_may10_inst.xlsx')
    df[["BHCCBT","BHCNTN"]] = df[["BHCCBT","BHCNTN"]].apply(lambda x: x.str.replace("/", "", regex=False))
    def convert_date_format(val):
        val = str(val).strip()
        if len(val) < 8:
            return val
        yyyy = val[0:4]
        mm = val[4:6]
        dd = val[6:8]
        suffix = val[8:] if len(val) > 8 else "0"
        return f"{mm}{dd}{yyyy}{suffix}"
    cols = ["BHDBDT", "BHBFRD", "BHBTOD"]
    for col in cols:
        df[col] = df[col].apply(convert_date_format)
    df.to_excel('backup.xlsx')
    def format_bhccbt(val):
        if pd.isna(val):
            return val
        val = str(val).strip()
        try:
            if float(val).is_integer():
                val = str(int(float(val)))
        except:
            pass
        if len(val) == 7 and val.isdigit():

            mm = val[0]
            dd = val[1:3]
            yyyy = val[3:]

            yy = yyyy[-2:]

            return yy + "0" + mm + dd 
        if len(val) == 8 and val.isdigit():
            mm = val[:2]
            dd = val[2:4]
            yyyy = val[4:]

            yy = yyyy[-2:]

            return yy + mm + dd 
        return val

    df["BHCCBT"] = df["BHCCBT"].apply(format_bhccbt)
    def fix_bhdbdt(val):
        if pd.isna(val):
            return val

        val = str(val).strip()
        try:
            if float(val).is_integer():
                val = str(int(float(val)))
        except:
            pass
        if len(val) == 9 and val.isdigit():

            yyyy = val[:4]
            mm = str(int(val[4:6]))
            dd = str(int(val[6:8]))

            return mm + dd + yyyy

        return val


    def fix_bhrecd(val):
        if pd.isna(val):
            return val
        val = str(val).strip()
        try:
            if float(val).is_integer():
                val = str(int(float(val)))
        except:
            pass

        if len(val) == 8 and val.isdigit():

            return val[:-1]

        return val


    df["BHDBDT"] = df["BHDBDT"].apply(fix_bhdbdt)
    df["BHDMRE"] = df["BHDMRE"].astype(str).str[:10]
    df['BHDMRE'] = df['BHDMRE'].apply(
        lambda x: ''
        if pd.isna(x) or str(x).strip().upper() == 'NONE'
        else x
    )
    df["BHDREL"] = df["BHDREL"].apply(
        lambda x: '' if str(x).strip() in ['18', '18.0'] else x
    )
    df["BHREFC"] = df["BHREFC"].astype(str).str[:3]
    df['BHDEPN'] = df['BHDEPN'].apply(
    lambda x: str(int(float(x))).zfill(2)
    if pd.notna(x) and str(x).strip() != ''
    else x
    )
    df['BHDREL'] = df['BHDREL'].apply(
    lambda x: str(int(float(x))).zfill(2)
    if pd.notna(x) and str(x).strip() != ''
    else x
    )
    df['BHSZIP'] = df['BHSZIP'].astype(str).str[:10]
    df['BHAMDG'] = df['BHAMDG'].apply(
    lambda x: str(x).split(':')[1] if pd.notna(x) and ':' in str(x) else x
    )
    df['BHDBDT'] = df['BHDBDT'].apply(
    lambda x: (
        str(x).replace('.0', '').strip()[0] + '0' + str(x).replace('.0', '').strip()[1:]
        if pd.notna(x) and len(str(x).replace('.0', '').strip()) == 6
        else str(x).replace('.0', '').strip()
    )
    )
    try:
        cols = ['BHDIO1', 'BHDIO2', 'BHDIO3', 'BHDIO4', 'BHDIO5']
        for col in cols:
            df[col] = df[col].apply(
                lambda x: (
                    '.'.join([str(x)[i:i+3] for i in range(0, len(str(x)), 3)])
                    if pd.notna(x) and str(x).strip() != '' and '.' not in str(x)
                    else x
                )
            )
    except:
        pass
    cols = ['BHBFRD', 'BHBTOD']
    for col in cols:
        df[col] = df[col].apply(
            lambda x: str(x).replace('.0', '')[:-1]
            if pd.notna(x) and str(x).replace('.0', '').strip() != ''
            else x
        )
    if filetype == 'P':
        df['BHAMDG'] = ''

    df['BHDEPN'] = df['BHDEPN'].apply(
    lambda x: str(int(float(x))).zfill(2)
    if pd.notna(x) and str(x).strip() != ''
    else x
    )
    df['BHCCBT'] = df['BHCCBT'].astype(str) + '0006'
    cols = ['mem_dob', 'dep_dob']
    for col in cols:
        df[col] = pd.to_datetime(df[col], format='%Y%m%d', errors='coerce') \
            .dt.strftime('%m%d%Y')
    df['BHMBDT'] = df['mem_dob']
    df['BHDBDT'] = df['dep_dob']
    df['BHPLSR'] = df['BHPLSR'].apply(
    lambda x: str(int(float(x))).zfill(2)
    if pd.notna(x) and str(x).strip() != ''
    else x
    )
    df['BHPSEQ'] = df['BHPSEQ'].apply(
    lambda x: str(int(float(x))).zfill(4)
    if pd.notna(x) and str(x).strip() != ''
    else x
    )
    try:
        cols = ['BHDIO1', 'BHDIO2', 'BHDIO3', 'BHDIO4', 'BHDIO5']
        for col in cols:
            df[col] = df[col].apply(
                lambda x: str(x).split(':')[0]
                if pd.notna(x) and '::::' in str(x)
                else x
            )
    except:
        pass

    dep_cols = ["BHDAD1", "BHDCTY", "BHDST", "BHDINT", "BHDZIP"]
    for idx, row in df.iterrows():
        try:
            if all(
                pd.isna(row[col]) or str(row[col]).strip() == ''
                for col in dep_cols
            ):
                for col in dep_cols:

                    member_col = col.replace("D", "M", 1)

                    if member_col in df.columns:
                        df.at[idx, col] = row[member_col]
        except:
            for col in dep_cols:
                member_col = col.replace("D", "M", 1)
                if member_col in df.columns:
                    df.at[idx, col] = row[member_col]
    if 'BHTAXO2' in df.columns:
        df.drop(columns=['BHTAXO2'],inplace=True)
    df['filename'] = filename
