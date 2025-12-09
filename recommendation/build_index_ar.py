import pickle
import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

# تحميل البيانات
df = pd.read_csv("enhanced_places_dataset_translated.csv")

# تحميل نموذج اللغة العربية
model_ar = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# إنشاء التضمينات للوصف العربي
embeddings_ar = model_ar.encode(df["semantic_description_ar"].fillna(""), show_progress_bar=True)
embeddings_ar = np.array(embeddings_ar).astype("float32")

# حفظ الفهرس العربي
index_ar = faiss.IndexFlatL2(embeddings_ar.shape[1])
index_ar.add(embeddings_ar)
faiss.write_index(index_ar, "tourism_index_ar.faiss")

# حفظ البيانات المرتبطة
with open("tourism_data_ar.pkl", "wb") as f:
    pickle.dump(df.to_dict(orient="records"), f)

print("✅ Arabic index and data saved successfully!")
