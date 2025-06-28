import pandas as pd
import numpy as np
import scipy.stats as stats
from collections import Counter
from datetime import datetime
import json, os

CSV_PATH = 'myntra_products_catalog.csv'
OUT_DIR = 'data'
os.makedirs(OUT_DIR, exist_ok=True)

def load_df():
    df = pd.read_csv(CSV_PATH)
    df['PrimaryColor'] = df['PrimaryColor'].astype(str).str.strip().str.lower()
    df['Price (INR)'] = df['Price (INR)'].round(-1).astype(int)
    return df

def save(name, data):
    path = os.path.join(OUT_DIR, f'{name}.json')
    with open(path, 'w') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
    return path

def pink_tax(df):
    wp = df[(df['Gender'] == 'Women') & (df['PrimaryColor'] == 'pink')]['Price (INR)']
    mb = df[(df['Gender'] == 'Men') & (df['PrimaryColor'] == 'blue')]['Price (INR)']
    stat = stats.ttest_ind(wp, mb, equal_var=False)
    return {
        'labels': ['Women-Pink', 'Men-Blue'],
        'values': [int(wp.mean()), int(mb.mean())],
        'p': round(float(stat.pvalue), 6)
    }

def classify_style(text):
    t = text.lower()
    if any(w in t for w in ['kurta', 'saree', 'lehenga', 'sherwani', 'dupatta', 'anarkali', 'palazzo']):
        return 'Ethnic'
    if any(w in t for w in ['blazer', 'suit', 'formal', 'waistcoat', 'tie', 'trouser', 'pant', 'coat', 'bandhgala']):
        return 'Formal'
    if any(w in t for w in ['sport', 'training', 'gym', 'active', 'athletic', 'legging', 'jogger', 'track', 'athleisure']):
        return 'Activewear'
    return 'Western Casual'

def style_gender(df):
    df['Style'] = (df['ProductName'] + ' ' + df['Description']).fillna('').apply(classify_style)
    subset = df[df['Gender'].isin(['Women', 'Men', 'Unisex'])]
    styles = ['Ethnic', 'Western Casual', 'Formal', 'Activewear']
    genders = ['Women', 'Men', 'Unisex']
    matrix = []
    for g in genders:
        counts = [int(subset[(subset['Gender'] == g) & (subset['Style'] == s)].shape[0]) for s in styles]
        matrix.append(counts)
    chi2, p, _, _ = stats.chi2_contingency(np.array(matrix))
    return {'genders': genders, 'styles': styles, 'matrix': matrix, 'p': round(float(p), 6)}

def color_palette(df):
    colors = df['PrimaryColor'].value_counts().head(10).index.tolist()
    res = {'colors': colors, 'Women': [], 'Men': []}
    for c in colors:
        res['Women'].append(int(df[(df['Gender'] == 'Women') & (df['PrimaryColor'] == c)].shape[0]))
        res['Men'].append(int(df[(df['Gender'] == 'Men') & (df['PrimaryColor'] == c)].shape[0]))
    return res

def price_ladder(df):
    top = df['ProductBrand'].value_counts().head(20).index
    med = df[df['ProductBrand'].isin(top)].groupby('ProductBrand')['Price (INR)'].median().sort_values()
    return {'brands': med.index.tolist(), 'median': med.astype(int).tolist()}

MASC = set('rugged strong bold tough men man guy dude his him'.split())
FEM = set('elegant pretty delicate women woman girl her she feminine lady'.split())

def unisex_tone(df):
    sub = df[df['Gender'].str.contains('Unisex')]
    counts = Counter({'Neutral': 0, 'Masculine': 0, 'Feminine': 0})
    for txt in (sub['ProductName'] + ' ' + sub['Description']).fillna('').str.lower():
        m = sum(w in txt for w in MASC)
        f = sum(w in txt for w in FEM)
        if m > f and m > 0:
            counts['Masculine'] += 1
        elif f > m and f > 0:
            counts['Feminine'] += 1
        else:
            counts['Neutral'] += 1
    return {'labels': ['Neutral', 'Masculine', 'Feminine'], 'counts': [counts['Neutral'], counts['Masculine'], counts['Feminine']]}

def photo_price(df):
    sample = df.sample(min(500, len(df)), random_state=42)
    points = sample[['Price (INR)', 'NumImages']].values.tolist()
    x = df['NumImages']
    y = df['Price (INR)']
    slope, intercept = np.polyfit(x, y, 1)
    return {'points': points, 'slope': round(float(slope), 3), 'intercept': round(float(intercept), 1)}

def dress_code(text):
    t = text.lower()
    if any(w in t for w in ['formal', 'suit', 'blazer', 'office', 'tie', 'trouser', 'pant', 'waistcoat']):
        return 'Formal'
    if any(w in t for w in ['party', 'evening', 'festive', 'wedding', 'sequin', 'occasion', 'dress']):
        return 'Party'
    if any(w in t for w in ['sport', 'jogger', 'legging', 'track', 'gym', 'athleisure']):
        return 'Athleisure'
    return 'Casual'

def dress_price(df):
    df['DressCode'] = (df['ProductName'] + ' ' + df['Description']).fillna('').apply(dress_code)
    codes = ['Formal', 'Party', 'Casual', 'Athleisure']
    stats_list = []
    for c in codes:
        vals = df[df['DressCode'] == c]['Price (INR)']
        q = vals.quantile([0, 0.25, 0.5, 0.75, 1]).tolist()
        stats_list.append([int(v) for v in q])
    return {'codes': codes, 'stats': stats_list}

STOP = set(['the', 'and', 'with', 'a', 'of', 'on', 'in', 'for', 'to', 'has', 'one', 'two', 'three', 'four', 'five', 'six'])

def roadster_keywords(df):
    sub = df[df['ProductBrand'].str.lower() == 'roadster']
    words = Counter()
    for txt in (sub['ProductName'] + ' ' + sub['Description']).fillna('').str.lower():
        for w in txt.replace('.', ' ').replace(',', ' ').split():
            if w.isalpha() and w not in STOP and len(w) > 2:
                words[w] += 1
    common = words.most_common(10)
    return {'words': [w for w, _ in common], 'counts': [int(c) for _, c in common]}

def charm_pricing(df):
    ends = df['Price (INR)'].astype(str).str.endswith('99')
    n99 = int(ends.sum())
    other = int((~ends).sum())
    return {'labels': ['₹99', 'Other'], 'counts': [n99, other]}

def color_price_heatmap(df):
    colors = df['PrimaryColor'].value_counts().head(10).index.tolist()
    bins = [0, 500, 1000, 2000, 3000, 5000, 1e9]
    buckets = ['0-500', '501-1000', '1001-2000', '2001-3000', '3001-5000', '5000+']
    matrix = []
    for c in colors:
        prices = df[df['PrimaryColor'] == c]['Price (INR)']
        cats = pd.cut(prices, bins, labels=buckets, include_lowest=True)
        counts = cats.value_counts().reindex(buckets, fill_value=0)
        matrix.append([int(v) for v in counts])
    return {'colors': colors, 'buckets': buckets, 'matrix': matrix}

def capsule_table(df):
    cheap = df[df['Price (INR)'] <= 1500].head(10)
    rows = []
    for _, r in cheap.iterrows():
        rows.append({'brand': r['ProductBrand'], 'name': r['ProductName'][:60], 'price': int(r['Price (INR)']), 'color': r['PrimaryColor'], 'gender': r['Gender']})
    return {'items': rows}

def main():
    df = load_df()
    files = {}
    files['pink_tax'] = save('pink_tax', pink_tax(df))
    files['style_gender'] = save('style_gender', style_gender(df))
    files['color_palette'] = save('color_palette', color_palette(df))
    files['price_ladder'] = save('price_ladder', price_ladder(df))
    files['unisex_tone'] = save('unisex_tone', unisex_tone(df))
    files['photo_price'] = save('photo_price', photo_price(df))
    files['dress_price'] = save('dress_price', dress_price(df))
    files['roadster_keywords'] = save('roadster_keywords', roadster_keywords(df))
    files['charm_pricing'] = save('charm_pricing', charm_pricing(df))
    files['color_price_heatmap'] = save('color_price_heatmap', color_price_heatmap(df))
    files['capsule'] = save('capsule', capsule_table(df))
    meta = {
        'total_items': int(df.shape[0]),
        'date': datetime.now().strftime('%Y-%m-%d'),
        'files': {os.path.basename(p): os.path.getsize(p) for p in files.values()}
    }
    save('meta', meta)

if __name__ == '__main__':
    main()
