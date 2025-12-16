import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

# 1) تحميل البيانات
df = pd.read_csv("enhanced_places_dataset_translated.csv")

# 2) ضمان إنو العمود ما فاضي
df["semantic_description"] = df["semantic_description"].fillna("")

# 3) تحميل نموذج الإنجليزي
model_en = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# 4) إنشاء التضمينات
embeddings_en = model_en.encode(
    df["semantic_description"].tolist(),
    show_progress_bar=True
).astype("float32")

# 5) حفظ الملف
np.save("embeddings_en.npy", embeddings_en)

print("✅ تم إنشاء ملف embeddings_en.npy بنجاح!")
