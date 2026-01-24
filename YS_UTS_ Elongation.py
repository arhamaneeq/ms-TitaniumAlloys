import pandas as pd
import io
import matplotlib.pyplot as plt
import numpy as np

csv_data = """alloy_id,phase_class,YS_MPa,UTS_MPa,elong_%
T6A4V_ar_A,alpha,979,1051,8.7
T6A4V_93060AC,alpha,1107,1186,12.6
T6A4V_96030AC,alpha,1122,1201,12.1
T6A4V_ar_B,alpha,886,997,14.7
T6A4V_91030WQ_580300AC,alpha,1025,1087,9.1
T6A4VO_925240FC,alpha,1108.5,1211.3,9.1
T6A4VO_955120WQ_550300AC,alpha,1352.4,1421.7,7.2
T6C5M5V4A_800120AC_600720AC,alpha,1181,1205,13.2
T6C5M5V4A_800120AC_550720AC,alpha,1241,1288,7.6
T6C5M5V4A_800120AC_450720AC,alpha,1368,1433,5.5
Ti55511_AM650,alpha,935,1042,19
Ti55511_AM750,alpha,1105,1178,8
IMI 834,Near-alpha,950,1060,9
Ti-1100,Near-alpha,920,1000,10
Ti-6Al-4V_ELI,alpha+beta,835,912,12.5
Ti-15Mo,beta,544,874,82
"""

def clean_numeric(val):
    if pd.isna(val) or str(val).lower() == 'not reported':
        return np.nan
    s = str(val).replace('–', '-').replace('—', '-')
    if '-' in s:
        try:
            parts = [float(p.strip()) for p in s.split('-') if p.strip()]
            return np.mean(parts)
        except: return np.nan
    try: return float(s)
    except: return np.nan

df = pd.read_csv(io.StringIO(csv_data))
for col in ['YS_MPa', 'UTS_MPa', 'elong_%']:
    df[col] = df[col].apply(clean_numeric)

plt.figure(figsize=(10, 6))
for phase, group in df.groupby('phase_class'):
    plt.scatter(group['elong_%'], group['UTS_MPa'], label=phase, s=100, edgecolors='white')

plt.title('Titanium Alloy Performance: UTS vs. Elongation')
plt.xlabel('Elongation (%)')
plt.ylabel('UTS (MPa)')
plt.legend(title="Phase Class")
plt.grid(True, linestyle='--', alpha=0.7)
plt.show()

plt.figure(figsize=(10, 6))
for phase, group in df.groupby('phase_class'):
    plt.scatter(group['YS_MPa'], group['UTS_MPa'], label=phase, s=100, edgecolors='white')

lims = [df['YS_MPa'].min() * 0.9, df['UTS_MPa'].max() * 1.1]
plt.plot(lims, lims, 'r--', alpha=0.5, label='YS = UTS')

plt.title('Strength Comparison: Yield vs. UTS')
plt.xlabel('Yield Strength (MPa)')
plt.ylabel('Ultimate Tensile Strength (MPa)')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.7)
plt.show()
