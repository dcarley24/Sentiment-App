import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import features
import textstat
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from collections import Counter
from PIL import Image
import pytesseract
from scipy import stats

app = Flask(__name__)
app.secret_key = "changeme"
DATABASE = 'posts.db'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

nltk.data.path.append('/home/doug/nltk_data')
nltk.download('vader_lexicon')
nltk.download('stopwords')
SIA = SentimentIntensityAnalyzer()
STOP_WORDS = set(stopwords.words('english'))

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def calculate_sincerity_features(text):
    return {
        "readability": features.readability_score(text),
        "buzzwords": features.buzzword_density(text),
        "pronouns": features.pronoun_presence(text),
        "stopwords": features.stopword_ratio(text),
        "caps": features.all_caps_ratio(text),
        "punctuation": features.punctuation_intensity(text),
        "emotion_ratio": features.sentiment_punctuation_balance(text),
        "verbosity": features.verbosity_score(text),
        "variance": features.sentence_length_variance(text),
        "engagement_elements_ratio": features.engagement_style_signal(text)
    }

def clean_ocr_text(text):
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        if line.count('|') > 0 and not any(s in line for s in ['||', '{', '}']):
            line = line.replace('|', 'I')
        cleaned.append(line)
    return '\n'.join(cleaned)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    text = request.form.get('post_text')
    if not text:
        return "No text submitted", 400
    scores = calculate_sincerity_features(text)
    final_score = round(sum(scores.values()) / len(scores) * 10, 1)
    return render_template('result.html', text=text, scores=scores, final_score=final_score)

@app.route('/records')
def records():
    conn = get_db_connection()
    posts = conn.execute("SELECT * FROM posts ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('records.html', posts=posts)

@app.route('/update_label/<int:post_id>', methods=['POST'])
def update_label(post_id):
    new_label = request.form.get('label')
    conn = get_db_connection()
    conn.execute("UPDATE posts SET label = ? WHERE id = ?", (new_label, post_id))
    conn.commit()
    conn.close()
    return redirect(url_for('records'))

@app.route('/analysis')
def analysis():
    conn = get_db_connection()
    posts = conn.execute("SELECT * FROM posts WHERE label IS NOT NULL").fetchall()
    conn.close()

    scored = []
    features_by_label = {0: [], 1: []}

    for row in posts:
        features_score = calculate_sincerity_features(row["text"])
        avg_score = sum(features_score.values()) / len(features_score)
        entry = {
            "id": row["id"],
            "label": row["label"],
            "text": row["text"],
            "score": round(avg_score * 10, 2),
            "features": features_score
        }
        scored.append(entry)
        features_by_label[row["label"]].append(features_score)

    def avg_feature(label, key):
        vals = [f[key] for f in features_by_label[label] if key in f]
        return round(sum(vals) / len(vals), 3) if vals else 0

    def avg_score(label):
        return round(sum(s["score"] for s in scored if s["label"] == label), 2)

    t_stat, p_value = stats.ttest_ind(
        [s["score"] for s in scored if s["label"] == 1],
        [s["score"] for s in scored if s["label"] == 0],
        equal_var=False
    )

    return render_template('analysis.html',
        genuine_count=len(features_by_label[1]),
        not_genuine_count=len(features_by_label[0]),
        avg_genuine_sentiment=avg_feature(1, "emotion_ratio"),
        avg_not_genuine_sentiment=avg_feature(0, "emotion_ratio"),
        avg_genuine_readability=avg_feature(1, "readability"),
        avg_not_genuine_readability=avg_feature(0, "readability"),
        avg_genuine_lexical_diversity=avg_feature(1, "verbosity"),
        avg_not_genuine_lexical_diversity=avg_feature(0, "verbosity"),
        avg_genuine_score=avg_score(1),
        avg_not_genuine_score=avg_score(0),
        avg_genuine_buzzwords=avg_feature(1, "buzzwords"),
        avg_not_genuine_buzzwords=avg_feature(0, "buzzwords"),
        avg_genuine_pronouns=avg_feature(1, "pronouns"),
        avg_not_genuine_pronouns=avg_feature(0, "pronouns"),
        avg_genuine_stopwords=avg_feature(1, "stopwords"),
        avg_not_genuine_stopwords=avg_feature(0, "stopwords"),
        avg_genuine_caps=avg_feature(1, "caps"),
        avg_not_genuine_caps=avg_feature(0, "caps"),
        avg_genuine_punctuation=avg_feature(1, "punctuation"),
        avg_not_genuine_punctuation=avg_feature(0, "punctuation"),
        avg_genuine_variance=avg_feature(1, "variance"),
        avg_not_genuine_variance=avg_feature(0, "variance"),
        avg_genuine_engagement=avg_feature(1, "engagement_elements_ratio"),
        avg_not_genuine_engagement=avg_feature(0, "engagement_elements_ratio"),
        t_stat=round(t_stat, 2),
        p_value=round(p_value, 4)
    )

@app.route('/curate', methods=['GET', 'POST'])
def curate():
    return render_template('curate.html')

@app.route('/save_selection', methods=['POST'])
def save_selection():
    selected_text = request.form.get('selected_text', '').strip()
    if not selected_text:
        return redirect(url_for('curate'))

    scores = calculate_sincerity_features(selected_text)
    final_score = round(sum(scores.values()) / len(scores) * 10, 1)
    #label = int(request.form.get('label', 1))

    try:
        conn = get_db_connection()
        conn.execute("INSERT INTO posts (text, label) VALUES (?, ?)", (selected_text, label))
        conn.commit()
    except sqlite3.Error as e:
        return f"Database error: {str(e)}", 500
    finally:
        conn.close()

    return render_template('curate.html',
                           extracted='',
                           last_text=selected_text,
                           scores=scores,
                           final_score=final_score,
                           label=label)

@app.route('/ocr_extract', methods=['POST'])
def ocr_extract():
    if 'ocr_image' not in request.files:
        return "No file uploaded", 400
    image = request.files['ocr_image']
    if image.filename == '':
        return "No file selected", 400
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(image.filename))
    image.save(filepath)
    try:
        text = pytesseract.image_to_string(Image.open(filepath))
        text = clean_ocr_text(text)
        os.remove(filepath)
        return render_template('curate.html', extracted=text)
    except Exception as e:
        return f"OCR failed: {str(e)}", 500

@app.route('/classify')
def classify():
    conn = get_db_connection()
    post = conn.execute("SELECT * FROM posts WHERE label IS NULL ORDER BY id LIMIT 1").fetchone()
    conn.close()
    if post:
        return render_template('classify.html', post=post)
    else:
        return render_template('classify.html', post=None, done=True)

@app.route('/label_post/<int:post_id>/<int:label>', methods=['POST'])
def label_post(post_id, label):
    conn = get_db_connection()
    conn.execute("UPDATE posts SET label = ? WHERE id = ?", (label, post_id))
    conn.commit()
    conn.close()
    return redirect(url_for('classify'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8443, ssl_context=('ssl/cert.pem', 'ssl/key.pem'), debug=True)
