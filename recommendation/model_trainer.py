import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import pickle

# تحميل البيانات
df = pd.read_csv('recommendation/enhanced_places_dataset_translated.csv')

# تحميل نموذجين: واحد للإنجليزية وواحد للعربية
model_en = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
model_ar = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

# توليد التضمينات لكل لغة
embeddings_en = model_en.encode(df['semantic_description'].fillna(""), show_progress_bar=True)
embeddings_ar = model_ar.encode(df['semantic_description_ar'].fillna(""), show_progress_bar=True)

# دمج التضمينات (نستخدم كليهما للبحث الثنائي)
combined_embeddings = np.concatenate((embeddings_en, embeddings_ar), axis=1)

# إنشاء فهرس FAISS للتوصية السريعة
index = faiss.IndexFlatL2(combined_embeddings.shape[1])
index.add(combined_embeddings)

# حفظ الفهرس والنموذج والبيانات
faiss.write_index(index, "recommendation/tourism_index.faiss")

with open("recommendation/tourism_data.pkl", "wb") as f:
    pickle.dump(df, f)

print("✅ تم إنشاء نموذج التوصية السياحي بنجاح!")
