import re
from typing import Optional
from src.models.period import Period

def parse_period(text: str) -> Period:
    raw = text.strip()
    raw_lower = raw.lower()
    
    # Pattern 1: Q1-2024, Q4-2023, Q1 2024, 4Q2024
    q_dash_match = re.search(r'(?:q([1-4])|([1-4])q)[\s\-_]*(?:fy\s*)?(\d{2,4})', raw_lower)
    if q_dash_match:
        quarter = int(q_dash_match.group(1) or q_dash_match.group(2))
        yr_str = q_dash_match.group(3)
        yr = int(yr_str) if len(yr_str) == 4 else 2000 + int(yr_str)
        start_dates = {1: f'{yr-1}-04-01', 2: f'{yr-1}-07-01', 3: f'{yr-1}-10-01', 4: f'{yr}-01-01'}
        end_dates = {1: f'{yr-1}-06-30', 2: f'{yr-1}-09-30', 3: f'{yr-1}-12-31', 4: f'{yr}-03-31'}
        return Period(
            period_id=f'Q{quarter}_FY{str(yr)[-2:]}',
            label=f'Q{quarter} FY{str(yr)[-2:]}',
            period_type='Quarter',
            start_date=start_dates[quarter],
            end_date=end_dates[quarter],
            is_restated='restated' in raw_lower
        )

    # Pattern 2: Twelve Months Ended / Year Ended
    if 'twelve months ended' in raw_lower or 'year ended' in raw_lower:
        yr_match = re.search(r'\b(20\d{2})\b', raw_lower)
        yr = int(yr_match.group(1)) if yr_match else 2024
        return Period(
            period_id=f'FY{str(yr)[-2:]}',
            label=f'FY{yr}',
            period_type='FiscalYear',
            start_date=f'{yr-1}-10-01',
            end_date=f'{yr}-09-30',
            is_restated='restated' in raw_lower
        )

    # Pattern 3: Three Months Ended / Quarter Ended
    if 'three months ended' in raw_lower or 'quarter ended' in raw_lower:
        yr_match = re.search(r'\b(20\d{2})\b', raw_lower)
        yr = int(yr_match.group(1)) if yr_match else 2024
        if 'september' in raw_lower or 'sep' in raw_lower:
            q_num = 4
        elif 'december' in raw_lower or 'dec' in raw_lower:
            q_num = 1
        elif 'march' in raw_lower or 'mar' in raw_lower:
            q_num = 2
        elif 'june' in raw_lower or 'jun' in raw_lower:
            q_num = 3
        else:
            q_num = 4
        return Period(
            period_id=f'Q{q_num}_FY{str(yr)[-2:]}',
            label=raw,
            period_type='Quarter',
            start_date=f'{yr}-01-01',
            end_date=f'{yr}-12-31',
            is_restated='restated' in raw_lower
        )

    # Pattern 4: Date like September 28, 2024 / Sep 30, 2023
    date_match = re.search(r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{1,2}),?\s+(20\d{2})', raw_lower)
    if date_match:
        yr = date_match.group(2)
        return Period(
            period_id=f'FY{yr[-2:]}',
            label=raw,
            period_type='PeriodEnded',
            start_date=f'{yr}-01-01',
            end_date=f'{yr}-12-31',
            is_restated='restated' in raw_lower
        )

    # Pattern 5: Fiscal Range 2023-24 / 2023-2024
    range_match = re.search(r'(?:fy\s*)?(\d{4})\s*[-–]\s*(\d{2,4})', raw_lower)
    if range_match:
        start_yr = int(range_match.group(1))
        end_yr_val = range_match.group(2)
        end_yr = int(end_yr_val) if len(end_yr_val) == 4 else (start_yr // 100) * 100 + int(end_yr_val)
        return Period(
            period_id=f'FY{str(end_yr)[-2:]}',
            label=f'FY{start_yr}-{str(end_yr)[-2:]}',
            period_type='FiscalYear',
            start_date=f'{start_yr}-04-01',
            end_date=f'{end_yr}-03-31',
            is_restated='restated' in raw_lower
        )

    # Pattern 6: FY24 / FY2024
    fy_match = re.search(r'\bfy\s*(\d{2,4})\b', raw_lower)
    if fy_match:
        yr_val = fy_match.group(1)
        end_yr = int(yr_val) if len(yr_val) == 4 else 2000 + int(yr_val)
        start_yr = end_yr - 1
        return Period(
            period_id=f'FY{str(end_yr)[-2:]}',
            label=f'FY{str(end_yr)[-2:]}',
            period_type='FiscalYear',
            start_date=f'{start_yr}-04-01',
            end_date=f'{end_yr}-03-31',
            is_restated='restated' in raw_lower
        )

    # Pattern 7: Standalone 4-digit Year (e.g. "2024", "2023")
    year_only_match = re.search(r'\b(20\d{2})\b', raw)
    if year_only_match:
        yr = year_only_match.group(1)
        return Period(
            period_id=f'FY{yr[-2:]}',
            label=yr,
            period_type='Year',
            start_date=f'{yr}-01-01',
            end_date=f'{yr}-12-31',
            is_restated='restated' in raw_lower
        )

    if 'as of' in raw_lower or 'as at' in raw_lower:
        yr_match = re.search(r'\b(20\d{2})\b', raw_lower)
        yr = yr_match.group(1) if yr_match else '2024'
        return Period(
            period_id=f'AS_OF_{yr}_03_31',
            label=raw,
            period_type='PointInTime',
            start_date=f'{yr}-03-31',
            end_date=f'{yr}-03-31',
            is_restated=False
        )

    return Period(
        period_id=raw.replace(' ', '_').upper()[:30],
        label=raw,
        period_type='Unknown',
        start_date=None,
        end_date=None,
        is_restated=False
    )
