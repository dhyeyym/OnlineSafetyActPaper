import os
for f in ['rq1/scripts/table_13.py', 'rq1/scripts/table_16.py', 'rq1/scripts/table_17.py', 'rq1/scripts/table_3.py']:
    txt = open(f).read()
    txt = txt.replace('pd.DataFrame({\"y\": values}, index=weeks)', 'pd.DataFrame({\"y\": values.values}, index=weeks.values)')
    open(f, 'w').write(txt)
    print(f'Fixed {f}')