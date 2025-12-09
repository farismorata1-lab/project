import pickle
import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

# تحميل البيانات
df = pd.read_csv("enhanced_places_dataset_translated.csv")

# تحميل نموذج اللغة الإنجليزية
model_en = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# إنشاء التضمينات للوصف الإنجليزي
embeddings_en = model_en.encode(df["semantic_description"].fillna(""), show_progress_bar=True)
embeddings_en = np.array(embeddings_en).astype("float32")

# حفظ الفهرس الإنجليزي
index_en = faiss.IndexFlatL2(embeddings_en.shape[1])
index_en.add(embeddings_en)
faiss.write_index(index_en, "tourism_index_en.faiss")

# حفظ البيانات المرتبطة
with open("tourism_data_en.pkl", "wb") as f:
    pickle.dump(df.to_dict(orient="records"), f)

print("✅ English index and data saved successfully!")
