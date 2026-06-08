import os
import pandas as pd
import re
from datetime import datetime

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
        # if seg == 'HCP':
        #     # print(f"damp {seg} {qualifier} {segment_str} {current_entity}")
        #     print(rules)
        # if flag < 50:
        #     # if 'BHTAXO' in current_data:
        #     print(current_data)
        # try:
        #     if  current_data['BHTXID'] == '340714585':
        #             print(f'this is current data {current_data}')
        # except:
        #     pass
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