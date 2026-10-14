import sys
sys.path.append('dashboard')
import db

df, err = db.query_phoenix_df("SELECT DISTINCT KHU_VUC FROM GIAO_DICH")
if err:
    print("Error:", err)
else:
    regions = df['KHU_VUC'].dropna().tolist()
    print("Total distinct regions:", len(regions))
    print("Sample regions:", regions[:15])

