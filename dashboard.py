import streamlit as st
import pandas as pd
from thefuzz import fuzz
import io

# ------------------------
# Required Columns
# ------------------------
REQUIRED_COLS = [
    "State_name", "District", "Block_Name", "Cluster_Name", "Cluster_Code",
    "Village_Code", "uniqueid", "childname", "fathername",
    "socialcategory", "gender", "age"
]

# ------------------------
# Utility Functions
# ------------------------
def remove_double_letters(p_word):
    return "".join([p_word[i] for i in range(len(p_word)) if i == len(p_word) - 1 or p_word[i] != p_word[i + 1]])

def replace_m_before_consonant(p_word):
    result = ""
    for i, c in enumerate(p_word):
        if c.upper() == 'M' and i < len(p_word) - 1 and p_word[i + 1].upper() not in ('A', 'E', 'I', 'O', 'U'):
            result += 'N'
        else:
            result += c
    return result

def fix_transliterations_level_1(p_word):
    if not isinstance(p_word, str): return ""
    v_word_upd = p_word.upper()

    v_word_upd = v_word_upd.replace('MOHAMMADA', 'MO').replace('MOHAMMAD', 'MO')
    v_word_upd = v_word_upd.replace("SIMHA", "SINGH")
    if "SINGH" not in v_word_upd:
        v_word_upd = v_word_upd.replace("SING", "SINGH")
    if v_word_upd != "DEVI":
        v_word_upd = v_word_upd.replace("DEVI", "")
    if v_word_upd not in ("BANO", "BANU"):
        v_word_upd = v_word_upd.replace("BANO", "").replace("BANU", "")
    
    v_word_upd = v_word_upd.replace("JJ", "GY").replace("CHH", "CH").replace("EE", "I")
    v_word_upd = v_word_upd.replace("OO", "U").replace("AI", "E").replace("AU", "O")
    v_word_upd = v_word_upd.replace("OU", "O").replace("EO", "EV").replace("PH", "F")
    v_word_upd = v_word_upd.replace("W", "V").replace("J", "Z").replace("SH", "S")
    v_word_upd = v_word_upd.replace("CA", "CHA").replace("KSH", "X").replace("KS", "X")
    v_word_upd = v_word_upd.replace("AY", "E")

    v_word_upd = remove_double_letters(v_word_upd)
    v_word_upd = replace_m_before_consonant(v_word_upd)

    return v_word_upd

def soundex(p_word):
    if not p_word or not isinstance(p_word, str):
        return None

    p_word = p_word.lower()
    v_letters = [char for char in p_word if char.isalpha()]
    if not v_letters:
        return None

    v_first_letter = v_letters[0]
    v_letters = [char for char in v_letters[1:] if char not in 'aeiouyhw']

    mapping = {
        'b': '1', 'f': '1', 'p': '1', 'v': '1',
        'c': '2', 'g': '2', 'j': '2', 'k': '2', 'q': '2', 's': '2', 'x': '2', 'z': '2',
        'd': '3', 't': '3',
        'l': '4',
        'm': '5', 'n': '5',
        'r': '6'
    }

    encoded = [mapping.get(c, '') for c in v_letters]

    # Remove consecutive duplicates
    filtered = []
    for ch in encoded:
        if not filtered or ch != filtered[-1]:
            filtered.append(ch)

    # Remove if first letter's code matches first digit
    first_digit = mapping.get(v_first_letter, '')
    if filtered and filtered[0] == first_digit:
        filtered = filtered[1:]

    filtered = filtered[:3]
    while len(filtered) < 3:
        filtered.append('0')

    return v_first_letter.upper() + ''.join(filtered)

def load_file(uploaded_file):
    """Load CSV or Excel"""
    if uploaded_file.name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith((".xls", ".xlsx")):
        return pd.read_excel(uploaded_file)
    else:
        return None

# ------------------------
# Streamlit App
# ------------------------
st.title("Advanced Fuzzy Matching Dashboard")

uploaded_df1 = st.file_uploader("Upload First Dataset (CSV/Excel)", type=["csv", "xls", "xlsx"])
uploaded_df2 = st.file_uploader("Upload Second Dataset (CSV/Excel)", type=["csv", "xls", "xlsx"])

category = st.selectbox("Choose Matching Category", ["D2D vs Enrolment", "D2D vs CIOOSG", "D2D vs GKP"])

if uploaded_df1 and uploaded_df2 and st.button("Run Fuzzy Matching"):
    df1 = load_file(uploaded_df1)
    df2 = load_file(uploaded_df2)

    if df1 is None or df2 is None:
        st.error("❌ Unsupported file type! Please upload CSV or Excel only.")
    else:
        # Column check
        missing1 = [c for c in REQUIRED_COLS if c not in df1.columns]
        missing2 = [c for c in REQUIRED_COLS if c not in df2.columns]

        if missing1:
            st.error(f"❌ First dataset is missing columns: {missing1}")
        elif missing2:
            st.error(f"❌ Second dataset is missing columns: {missing2}")
        else:
            df1 = df1.fillna("")
            df2 = df2.fillna("")

            # Merge on Village_Code
            new1 = df1.merge(df2, on="Village_Code", suffixes=("_old1", "_new1"))
            if new1.empty:
                st.warning("⚠️ No records matched on Village_Code between the two datasets.")
            else:
                # === Your Exact Scoring Logic ===
                new1.fillna('', inplace=True)
                a = len(new1)
                scores = [0]*a
                childname_score, fathername_score, age_score, gender_score, soc_cat_score = [0]*a, [0]*a, [0]*a, [0]*a, [0]*a

                for i in new1.index:
                    # Childname logic
                    if any([
                        soundex(new1['childname_old1'][i]) == soundex(new1['childname_new1'][i]),
                        soundex(new1['childname_old1'][i].replace(" ", "")) == soundex(new1['childname_new1'][i].replace(" ", "")),
                        soundex(new1['childname_old1'][i].split()[0] if new1['childname_old1'][i] else "") ==
                        soundex(new1['childname_new1'][i].split()[0] if new1['childname_new1'][i] else ""),
                        soundex(fix_transliterations_level_1(new1['childname_old1'][i].replace(" ", ""))) ==
                        soundex(fix_transliterations_level_1(new1['childname_new1'][i].replace(" ", "")))
                    ]):
                        scores[i] += 200
                        childname_score[i] += 200

                    sims = [
                        fuzz.WRatio(new1['childname_old1'][i], new1['childname_new1'][i]),
                        fuzz.WRatio(new1['childname_old1'][i].replace(" ", ""), new1['childname_new1'][i].replace(" ", "")),
                        fuzz.WRatio(new1['childname_old1'][i].split()[0] if new1['childname_old1'][i] else "", new1['childname_new1'][i].split()[0] if new1['childname_new1'][i] else ""),
                        fuzz.WRatio(fix_transliterations_level_1(new1['childname_old1'][i].replace(" ", "")), fix_transliterations_level_1(new1['childname_new1'][i].replace(" ", "")))
                    ]
                    childname_score[i] += 20 * max(s//10 for s in sims)
                    scores[i] += childname_score[i]

                    # Gender
                    if new1['gender_old1'][i] == new1['gender_new1'][i]:
                        scores[i] += 200
                        gender_score[i] += 200

                    # Fathername logic
                    if any([
                        soundex(new1['fathername_old1'][i]) == soundex(new1['fathername_new1'][i]),
                        soundex(new1['fathername_old1'][i].replace(" ", "")) == soundex(new1['fathername_new1'][i].replace(" ", "")),
                        soundex(new1['fathername_old1'][i].split()[0] if new1['fathername_old1'][i] else "") ==
                        soundex(new1['fathername_new1'][i].split()[0] if new1['fathername_new1'][i] else ""),
                        soundex(fix_transliterations_level_1(new1['fathername_old1'][i].replace(" ", ""))) ==
                        soundex(fix_transliterations_level_1(new1['fathername_new1'][i].replace(" ", "")))
                    ]):
                        scores[i] += 200
                        fathername_score[i] += 200

                    sims = [
                        fuzz.WRatio(new1['fathername_old1'][i], new1['fathername_new1'][i]),
                        fuzz.WRatio(new1['fathername_old1'][i].replace(" ", ""), new1['fathername_new1'][i].replace(" ", "")),
                        fuzz.WRatio(new1['fathername_old1'][i].split()[0] if new1['fathername_old1'][i] else "", new1['fathername_new1'][i].split()[0] if new1['fathername_new1'][i] else ""),
                        fuzz.WRatio(fix_transliterations_level_1(new1['fathername_old1'][i].replace(" ", "")), fix_transliterations_level_1(new1['fathername_new1'][i].replace(" ", "")))
                    ]
                    fathername_score[i] += 20 * max(s//10 for s in sims)
                    scores[i] += fathername_score[i]

                    # Age
                    try:
                        age_diff = abs(int(new1['age_new1'][i]) - int(new1['age_old1'][i]))
                        score = max(0, 10 * (9 - age_diff))
                    except:
                        score = 0
                    scores[i] += score
                    age_score[i] += score

                    # Social category
                    if new1['socialcategory_old1'][i] == new1['socialcategory_new1'][i]:
                        scores[i] += 110
                        soc_cat_score[i] += 110

                # Final DataFrame
                new1["childname_score"] = childname_score
                new1["fathername_score"] = fathername_score
                new1["gender_score"] = gender_score
                new1["age_score"] = age_score
                new1["soc_cat_score"] = soc_cat_score
                new1["total_score"] = scores

                # Show results
                st.success("✅ Fuzzy Matching Completed")
                st.dataframe(new1.sort_values("total_score", ascending=False).head(50))

                # Download results
                buffer = io.BytesIO()
                new1.to_csv(buffer, index=False)
                buffer.seek(0)
                st.download_button("Download Full Results", buffer, file_name="fuzzy_matching_results.csv", mime="text/csv")
