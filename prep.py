import pandas as pd
import numpy as np
import os
import json
import re
from collections import Counter
from scipy import stats
from datetime import datetime

CSV_FILE = 'myntra_products_catalog.csv'
DATA_DIR = 'data'
os.makedirs(DATA_DIR, exist_ok=True)

def load_data():
    df = pd.read_csv(CSV_FILE)
    return df

STYLE_KEYWORDS = {
    'Ethnic': ['kurta','saree','sari','lehenga','sherwani','dupatta','ethnic','jhumka','dhoti'],
    'Western Casual': ['jeans','t-shirt','tee','dress','casual','skirt','top','jacket','sweater','shorts','hoodie','sweatshirt'],
    'Formal': ['suit','blazer','formal','shirt','trousers','bandhgala','tie','waistcoat'],
    'Activewear': ['sports','active','track','running','gym','athletic','sneakers','leggings','training']
}

DRESS_KEYWORDS = {
    'Formal': ['formal','suit','blazer','bandhgala','waistcoat','gown','trousers'],
    'Party': ['party','evening','cocktail','festive','wedding','embellished','sequined'],
    'Casual': ['casual','t-shirt','jeans','shorts','polo','regular'],
    'Athleisure': ['track','sports','running','gym','yoga','athletic','sweat','active']
}

MASCULINE_WORDS = ['rugged','bold','strong','adventure','utility','tough']
FEMININE_WORDS = ['elegant','chic','graceful','pretty','delicate','floral','stylish']
STOPWORDS = set(['the','and','with','for','your','this','that','from','made','size','color','colour','wash','design','fit','regular','pack','set'])

def categorize_style(text):
    t = text.lower()
    for style, words in STYLE_KEYWORDS.items():
        for w in words:
            if w in t:
                return style
    return 'Western Casual'

def categorize_dress(text):
    t = text.lower()
    for dc, words in DRESS_KEYWORDS.items():
        for w in words:
            if w in t:
                return dc
    return 'Casual'

def tone_from_text(text):
    t = str(text).lower()
    if any(w in t for w in MASCULINE_WORDS):
        return 'Masculine'
    if any(w in t for w in FEMININE_WORDS):
        return 'Feminine'
    return 'Neutral'

def save_json(name, obj):
    path = os.path.join(DATA_DIR, name)
    with open(path, 'w') as f:
        json.dump(obj, f, separators=(',', ':'))
    return path

def main():
    df = load_data()

    # Pink Tax
    women_pink = df[(df['Gender']=='Women') & (df['PrimaryColor'].str.contains('Pink', case=False, na=False))]
    men_blue = df[(df['Gender']=='Men') & (df['PrimaryColor'].str.contains('Blue', case=False, na=False))]
    wp_mean = round(women_pink['Price (INR)'].mean()/10)*10 if len(women_pink) else 0
    mb_mean = round(men_blue['Price (INR)'].mean()/10)*10 if len(men_blue) else 0
    if len(women_pink) and len(men_blue):
        _, pval = stats.ttest_ind(women_pink['Price (INR)'], men_blue['Price (INR)'], equal_var=False)
        pval = round(float(pval), 4)
    else:
        pval = None
    save_json('pink_tax.json', {'women_mean': int(wp_mean), 'men_mean': int(mb_mean), 'p_value': pval})

    # Style x Gender
    df['Style'] = (df['ProductName'] + ' ' + df['Description']).apply(categorize_style)
    df['Gender2'] = df['Gender'].replace({'Boys':'Kids','Girls':'Kids','Unisex Kids':'Kids'})
    styles = list(STYLE_KEYWORDS.keys())
    genders = ['Women','Men','Unisex','Kids']
    matrix = []
    for g in genders:
        counts = df[df['Gender2']==g]['Style'].value_counts().reindex(styles, fill_value=0)
        matrix.append(counts.astype(int).tolist())
    save_json('style_gender.json', {'styles': styles, 'genders': genders, 'matrix': matrix})

    # Top-10 Colour Palette by Gender
    top_colors = df['PrimaryColor'].value_counts().head(10).index.tolist()
    palette = []
    for color in top_colors:
        m = int(((df['Gender']=='Men') & (df['PrimaryColor']==color)).sum())
        w = int(((df['Gender']=='Women') & (df['PrimaryColor']==color)).sum())
        palette.append({'color': color, 'men': m, 'women': w})
    save_json('palette_gender.json', palette)

    # Price Ladder: Top-20 Brands
    med = df.groupby('ProductBrand')['Price (INR)'].median().round(-1).sort_values(ascending=False).head(20)
    brands = [{'brand': b, 'median_price': int(v)} for b,v in med.items()]
    save_json('price_ladder.json', brands)

    # Unisex Language Tone
    u = df[df['Gender'].str.contains('Unisex')].copy()
    u['Tone'] = u['Description'].fillna('').apply(tone_from_text)
    tone_counts = u['Tone'].value_counts().reindex(['Neutral','Masculine','Feminine'], fill_value=0).astype(int).to_dict()
    save_json('unisex_tone.json', tone_counts)

    # Photo Count vs Price
    sample = df[['NumImages','Price (INR)']].dropna().sample(n=min(500,len(df)), random_state=42)
    slope, intercept = np.polyfit(sample['NumImages'], sample['Price (INR)'], 1)
    points = sample.round({'Price (INR)':-1}).astype(int).values.tolist()
    save_json('photos_price.json', {'points': points, 'slope': float(round(slope,3)), 'intercept': float(round(intercept,1))})

    # Dress Code vs Price
    df['DressCode'] = (df['ProductName'] + ' ' + df['Description']).apply(categorize_dress)
    codes = ['Formal','Party','Casual','Athleisure']
    boxes = []
    for c in codes:
        prices = df[df['DressCode']==c]['Price (INR)']
        if len(prices)==0:
            continue
        q = prices.quantile([0,0.25,0.5,0.75,1]).round(-1)
        boxes.append({'code': c, 'min': int(q.iloc[0]), 'q1': int(q.iloc[1]), 'median': int(q.iloc[2]), 'q3': int(q.iloc[3]), 'max': int(q.iloc[4])})
    save_json('dress_price.json', boxes)

    # Brand-Voice Keywords (Roadster)
    road_desc = ' '.join(df[df['ProductBrand'].str.contains('Roadster', case=False, na=False)]['Description'].dropna().tolist()).lower()
    words = re.findall(r'[a-z]{3,}', road_desc)
    words = [w for w in words if w not in STOPWORDS]
    freq = Counter(words)
    top = [{'word': w, 'count': int(c)} for w,c in freq.most_common(10)]
    save_json('roadster_words.json', top)

    # Charm Pricing Prevalence
    charm = df['Price (INR)'].apply(lambda x: str(int(x)).endswith('99')).sum()
    other = len(df) - charm
    save_json('charm_pricing.json', {'ending_99': int(charm), 'other': int(other)})

    # Colour x Price Heatmap
    bins = [0,500,1000,1500,2000,3000,1e9]
    labels = ['<500','500-999','1000-1499','1500-1999','2000-2999','>=3000']
    df['price_bin'] = pd.cut(df['Price (INR)'], bins=bins, labels=labels, right=False)
    top_colors = df['PrimaryColor'].value_counts().head(10).index.tolist()
    heat = df[df['PrimaryColor'].isin(top_colors)].pivot_table(index='PrimaryColor', columns='price_bin', aggfunc='size', fill_value=0).reindex(index=top_colors, columns=labels, fill_value=0)
    save_json('color_price_heat.json', {'colors': top_colors, 'buckets': labels, 'matrix': heat.astype(int).values.tolist()})

    # Capsule Wardrobe <= 1500
    capsule = df[df['Price (INR)']<=1500].sort_values('Price (INR)').head(10)
    capsule['Price (INR)'] = capsule['Price (INR)'].round(-1).astype(int)
    table = capsule[['ProductName','ProductBrand','PrimaryColor','Price (INR)']].to_dict(orient='records')
    save_json('capsule.json', table)

    # Meta information
    meta = {
        'rows': int(len(df)),
        'brands': int(df['ProductBrand'].nunique()),
        'generated': datetime.utcnow().isoformat(timespec='seconds'),
        'files': {}
    }
    for fname in os.listdir(DATA_DIR):
        path = os.path.join(DATA_DIR, fname)
        meta['files'][fname] = os.path.getsize(path)
    save_json('meta.json', meta)

if __name__ == '__main__':
    main()
