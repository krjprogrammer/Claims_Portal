from datetime import datetime, date 
from django.db.models import Q
from .models import Member

def calculate_match_candidates(claim):
    """
    Modular matching helper logic (no changes to existing scoring engine logic).
    Searches Member registry DB and calculates weights:
    - SSN: +35%
    - Member ID: +25%
    - DOB: +20%
    - Name Similarity: +20%
    """
    query = Q(ssn=claim.ssn) | Q(member_id=claim.member_id) | Q(full_name__icontains=claim.patient_name.split()[0])
    candidates = Member.objects.filter(query)
    
    results = []
    for member in candidates:
        score = 0
        why_matched = []
        
        # SSN match: 35%
        if member.ssn and claim.ssn and member.ssn.strip() == claim.ssn.strip():
            score += 35
            why_matched.append("SSN")
            
        # Member ID match: 25%
        if member.member_id and claim.member_id and member.member_id.strip() == claim.member_id.strip():
            score += 25
            why_matched.append("Member ID")
            
        # DOB match: 20%
        if member.dob == claim.dob:
            score += 20
            why_matched.append("DOB")
            
        # Name match: 20%
        claim_name_parts = set(claim.patient_name.lower().split())
        member_name_parts = set(member.full_name.lower().split())
        common_parts = claim_name_parts.intersection(member_name_parts)
        if common_parts:
            score += 20
            why_matched.append("Name")
        
        masked_ssn = f"XXX-XX-{member.ssn[-4:]}" if member.ssn and len(member.ssn) >= 4 else "XXX-XX-XXXX"
        
        results.append({
            'id': member.id,
            'ssn': masked_ssn,
            'seq': member.sequence_no,
            'full_name': member.full_name,
            'dob': member.dob.strftime('%m/%d/%Y') if member.dob else "",
            'relationship': member.relationship,
            'eligibility_status': member.eligibility_status,
            'client': member.client_code,
            'match_score': f"{score}%",
            'score_num': score,
            'why_matched': ", ".join(why_matched) if why_matched else "None"
        })
        
    return sorted(results, key=lambda x: x['score_num'], reverse=True)


def build_comparison_matrix(claim, member):
    """
    Generates comparison matrix between incoming claim values and candidate member.
    Bypasses serializers by building python dictionaries.
    """
    fields_to_compare = [
        ('Patient Name', 'patient_name', 'full_name'),
        ('DOB', 'dob', 'dob'),
        ('Gender', 'gender', 'gender'),
        ('Relationship', 'relationship', 'relationship'),
        ('Member ID', 'member_id', 'member_id'),
        ('SSN', 'ssn', 'ssn'),
    ]
    
    comparison_list = []
    for label, claim_field, member_field in fields_to_compare:
        claim_val = getattr(claim, claim_field, None)
        member_val = getattr(member, member_field, None) if member else None
        
        # Date string formatting
        if claim_val and isinstance(claim_val, (datetime, date)):
            claim_val = claim_val.strftime('%m/%d/%Y')
        elif claim_val and not isinstance(claim_val, str):
            claim_val = str(claim_val)
            
        if member_val and isinstance(member_val, (datetime, date)):
            member_val = member_val.strftime('%m/%d/%Y')
        elif member_val and not isinstance(member_val, str):
            member_val = str(member_val)
        
        # Format string dates if they are DB format strings
        if label == 'DOB':
            if isinstance(claim_val, str) and '-' in claim_val:
                try:
                    claim_val = datetime.strptime(claim_val, '%Y-%m-%d').strftime('%m/%d/%Y')
                except ValueError:
                    pass
            if isinstance(member_val, str) and '-' in member_val:
                try:
                    member_val = datetime.strptime(member_val, '%Y-%m-%d').strftime('%m/%d/%Y')
                except ValueError:
                    pass
        
        # Mask SSN
        if label == 'SSN':
            if claim_val and len(claim_val) >= 4:
                claim_val = f"XXX-XX-{claim_val[-4:]}"
            if member_val and len(member_val) >= 4:
                member_val = f"XXX-XX-{member_val[-4:]}"
        
        is_match = False
        if claim_val and member_val:
            is_match = str(claim_val).strip().lower() == str(member_val).strip().lower()
            
        comparison_list.append({
            'field': label,
            'claim_value': claim_val or "",
            'database_value': member_val or "",
            'match': is_match
        })
        
    return comparison_list
