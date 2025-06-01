import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
import textstat

nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

STOPWORDS = set(stopwords.words('english'))
BUZZWORDS = {
    "excited", "humbled", "synergy", "innovation", "passionate",
    "thrilled", "mission-driven", "disruptive", "amazing", "journey"
}

def readability_score(text):
    score = textstat.flesch_reading_ease(text)
    return max(0.0, min(score / 100.0, 1.0))

def buzzword_density(text):
    tokens = word_tokenize(text.lower())
    if not tokens:
        return 1.0
    buzz_count = sum(1 for w in tokens if w in BUZZWORDS)
    return max(0.0, 1.0 - (buzz_count / len(tokens)))

def pronoun_presence(text):
    tokens = word_tokenize(text.lower())
    i_count = tokens.count("i")
    we_count = tokens.count("we")
    total = i_count + we_count
    if total == 0:
        return 0.5
    elif total > 3:
        return 0.3
    else:
        return 0.9

def stopword_ratio(text):
    tokens = word_tokenize(text.lower())
    if not tokens:
        return 0.5
    stop_count = sum(1 for w in tokens if w in STOPWORDS)
    ratio = stop_count / len(tokens)
    return min(max(ratio, 0.0), 1.0)

def all_caps_ratio(text):
    tokens = word_tokenize(text)
    if not tokens:
        return 1.0
    cap_count = sum(1 for t in tokens if t.isupper() and len(t) > 1)
    return 1.0 - min(cap_count / len(tokens), 1.0)

def punctuation_intensity(text):
    intense = len(re.findall(r'[!?]{2,}|\.{3,}', text))
    return 1.0 - min(intense / 3.0, 1.0)

def sentiment_punctuation_balance(text):
    exclam = text.count("!")
    period = text.count(".")
    if exclam == 0:
        return 1.0
    ratio = exclam / (period + 1)
    return 1.0 - min(ratio / 3.0, 1.0)

def verbosity_score(text):
    words = len(word_tokenize(text))
    if words <= 100:
        return 1.0
    elif words >= 500:
        return 0.0
    else:
        return 1.0 - ((words - 100) / 400)

def sentence_length_variance(text):
    sentences = sent_tokenize(text)
    if len(sentences) < 2:
        return 0.5
    lengths = [len(word_tokenize(s)) for s in sentences]
    mean = sum(lengths) / len(lengths)
    variance = sum((x - mean) ** 2 for x in lengths) / len(lengths)
    norm = min(variance / 25.0, 1.0)
    return 1.0 - norm

def engagement_style_signal(text):
    link_count = text.lower().count("http")
    mention_count = text.count("@")
    hashtag_count = text.count("#")
    total = link_count + mention_count + hashtag_count
    return min(total / 5.0, 1.0)
