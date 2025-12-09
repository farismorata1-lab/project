import pickle
import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

# تحميل البيانات
df = pd.read_csv("enhanced_places_dataset_translated.csv")

df["semantic_description_ar"] = df["semantic_description_ar"].fillna(df["semantic_description"])


# تحميل نموذج اللغة العربية
model_ar = SentenceTransformer("sentence-transformers/paraphrase-multilingual-mpnet-base-v2")

# إنشاء التضمينات للوصف العربي
embeddings_ar = model_ar.encode(
    df["semantic_description_ar"].fillna(""),
    show_progress_bar=True
).astype("float32")

# حفظ التضمينات كملف فعلي
np.save("embeddings_ar.npy", embeddings_ar)

# حفظ فهرس FAISS
index_ar = faiss.IndexFlatL2(embeddings_ar.shape[1])
index_ar.add(embeddings_ar)
faiss.write_index(index_ar, "tourism_index_ar.faiss")

# حفظ البيانات
with open("tourism_data_ar.pkl", "wb") as f:
    pickle.dump(df.to_dict(orient="records"), f)

print("✅ Arabic embeddings + FAISS + data saved successfully!")
