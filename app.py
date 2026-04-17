import streamlit as st
import anthropic
import base64
import os

SYSTEM_PROMPT = """
あなたは骨折回復をサポートする食事アドバイザーです。
ユーザーは首（頸椎）の骨折から回復中です。

骨癒合を最速化するために以下の栄養素を優先してください：
- タンパク質（骨の土台・コラーゲン合成）
- カルシウム（骨の主成分）
- ビタミンD（カルシウム吸収を3〜5倍にする）
- ビタミンK2（カルシウムを骨に誘導）
- ビタミンC（コラーゲン合成に必須）
- マグネシウム（骨の強度）
- 亜鉛（骨芽細胞の働きを助ける）
- オメガ3脂肪酸（炎症を抑える）

避けるべきもの：過剰なアルコール・カフェイン・高塩分・加工食品

回答のルール：
- 語尾は「食え」「頼め」「とれ」など命令形で。友達に話すようにズバッと言う
- 理由は1行で添える（長い説明は不要）
- おすすめ3〜5品を具体的に。各品目に絵文字をつける
- 絶対避けるものがあれば最後に⚠️で1行
- 日本語で答える
"""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans JP', sans-serif;
}

/* 背景 */
.stApp {
    background: linear-gradient(135deg, #0a0a0a 0%, #111827 50%, #0a0a0a 100%);
}

/* メインヘッダー */
.main-header {
    text-align: center;
    padding: 2rem 0 1rem;
}
.main-title {
    font-size: 3.5rem;
    font-weight: 900;
    background: linear-gradient(90deg, #f97316, #ef4444, #f97316);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shine 3s linear infinite;
    letter-spacing: -2px;
}
.main-subtitle {
    color: #6b7280;
    font-size: 0.95rem;
    margin-top: -0.5rem;
}
@keyframes shine {
    to { background-position: 200% center; }
}

/* タブのカスタマイズ */
.stTabs [data-baseweb="tab-list"] {
    background: #1f2937;
    border-radius: 12px;
    padding: 4px;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    color: #9ca3af;
    border-radius: 8px;
    font-weight: 700;
    padding: 0.6rem 1.5rem;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #f97316, #ef4444) !important;
    color: white !important;
}

/* 入力フィールド */
.stTextInput input {
    background: #1f2937 !important;
    border: 2px solid #374151 !important;
    border-radius: 12px !important;
    color: #f9fafb !important;
    font-size: 1.1rem !important;
    padding: 0.8rem 1rem !important;
}
.stTextInput input:focus {
    border-color: #f97316 !important;
    box-shadow: 0 0 0 3px rgba(249,115,22,0.2) !important;
}

/* ボタン */
.stButton button[kind="primary"] {
    background: linear-gradient(135deg, #f97316, #ef4444) !important;
    border: none !important;
    border-radius: 12px !important;
    color: white !important;
    font-weight: 900 !important;
    font-size: 1.1rem !important;
    padding: 0.8rem 2rem !important;
    width: 100% !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 20px rgba(249,115,22,0.4) !important;
}
.stButton button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 30px rgba(249,115,22,0.6) !important;
}

/* 結果カード */
.result-card {
    background: #1f2937;
    border: 1px solid #374151;
    border-left: 4px solid #f97316;
    border-radius: 12px;
    padding: 1.5rem;
    margin-top: 1rem;
    color: #f9fafb;
    line-height: 1.8;
    font-size: 1.05rem;
}

/* 栄養素バッジ */
.nutrient-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 1rem;
}
.nutrient-badge {
    background: #374151;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.8rem;
    color: #d1d5db;
}

/* サイドバー */
section[data-testid="stSidebar"] {
    background: #111827 !important;
}
section[data-testid="stSidebar"] .stTextInput input {
    font-family: monospace;
    font-size: 0.8rem !important;
}

/* ファイルアップローダー */
.stFileUploader {
    border: 2px dashed #374151 !important;
    border-radius: 12px !important;
    background: #1f2937 !important;
    padding: 1rem !important;
}

/* spinner */
.stSpinner > div {
    border-top-color: #f97316 !important;
}

/* success box */
.stAlert[data-baseweb="notification"] {
    background: #1f2937 !important;
    border-color: #f97316 !important;
}

/* 画像 */
.stImage img {
    border-radius: 12px;
    border: 2px solid #374151;
}
</style>
"""

def get_client():
    api_key = os.environ.get("ANTHROPIC_API_KEY") or st.session_state.get("api_key")
    if not api_key:
        return None
    return anthropic.Anthropic(api_key=api_key)

def suggest_restaurant(client, restaurant_name: str) -> str:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"今から「{restaurant_name}」に行く。骨折回復のために何を頼むべきか教えて。"
        }]
    )
    return response.content[0].text

def suggest_from_photo(client, image_bytes: bytes, mime_type: str) -> str:
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": image_b64,
                    }
                },
                {
                    "type": "text",
                    "text": "これが今日の朝ごはん。骨折回復のために昼と夜は何を食えばいいか教えて。朝で足りてる栄養・足りてない栄養も教えて。"
                }
            ]
        }]
    )
    return response.content[0].text

# ==================== UI ====================

st.set_page_config(
    page_title="骨メシ",
    page_icon="🦴",
    layout="centered"
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ヘッダー
st.markdown("""
<div class="main-header">
    <div class="main-title">🦴 骨メシ</div>
    <div class="main-subtitle">骨折回復を最速化する食事アドバイザー</div>
</div>
""", unsafe_allow_html=True)

# サイドバー
with st.sidebar:
    st.markdown("### ⚙️ 設定")
    api_key_input = st.text_input(
        "Anthropic API キー",
        type="password",
        value=os.environ.get("ANTHROPIC_API_KEY", ""),
        placeholder="sk-ant-..."
    )
    if api_key_input:
        st.session_state["api_key"] = api_key_input
        st.markdown("✅ APIキー設定済み")

    st.markdown("---")
    st.markdown("**🔬 骨癒合に必要な栄養素**")
    nutrients = [
        ("🥩", "タンパク質", "骨の土台"),
        ("🥛", "カルシウム", "骨の主成分"),
        ("☀️", "ビタミンD", "Ca吸収3〜5倍"),
        ("🌿", "ビタミンK2", "Caを骨へ誘導"),
        ("🍊", "ビタミンC", "コラーゲン合成"),
        ("🫘", "マグネシウム", "骨の強度"),
        ("🦪", "亜鉛", "骨芽細胞を助ける"),
        ("🐟", "オメガ3", "炎症を抑える"),
    ]
    for icon, name, desc in nutrients:
        st.markdown(f"{icon} **{name}** — {desc}")

client = get_client()
if not client:
    st.markdown("""
    <div style="background:#1f2937;border:1px solid #f97316;border-radius:12px;padding:1.5rem;text-align:center;color:#f9fafb;margin-top:2rem;">
        <div style="font-size:2rem">🔑</div>
        <div style="font-weight:700;margin-top:0.5rem">APIキーを入力してください</div>
        <div style="color:#9ca3af;font-size:0.9rem;margin-top:0.3rem">左のサイドバーから入力</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

tab1, tab2 = st.tabs(["🍽️ 外食モード", "📸 朝食写真モード"])

# ==================== 外食モード ====================
with tab1:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 店名を入れるだけで「これ頼め」が出る")

    restaurant = st.text_input(
        "",
        placeholder="例：吉野家　サイゼリヤ　マクドナルド　焼肉屋...",
        key="restaurant_input",
        label_visibility="collapsed"
    )

    if st.button("何頼む？", type="primary", key="btn_restaurant"):
        if not restaurant.strip():
            st.error("店名を入れてください")
        else:
            with st.spinner(f"「{restaurant}」のメニューを分析中..."):
                result = suggest_restaurant(client, restaurant)
            st.markdown(f"""
            <div class="result-card">
            {result.replace(chr(10), '<br>')}
            </div>
            """, unsafe_allow_html=True)

# ==================== 朝食写真モード ====================
with tab2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 朝ごはんの写真を送ると「昼夜はこれ食え」が出る")

    uploaded = st.file_uploader(
        "",
        type=["jpg", "jpeg", "png", "webp"],
        key="photo_input",
        label_visibility="collapsed"
    )

    if uploaded:
        st.image(uploaded, caption="📷 朝ごはん", use_container_width=True)
        if st.button("昼と夜は何食う？", type="primary", key="btn_photo"):
            mime_map = {
                "jpg": "image/jpeg", "jpeg": "image/jpeg",
                "png": "image/png", "webp": "image/webp"
            }
            ext = uploaded.name.rsplit(".", 1)[-1].lower()
            mime = mime_map.get(ext, "image/jpeg")
            with st.spinner("朝食を分析して昼夜メニューを考え中..."):
                result = suggest_from_photo(client, uploaded.read(), mime)
            st.markdown(f"""
            <div class="result-card">
            {result.replace(chr(10), '<br>')}
            </div>
            """, unsafe_allow_html=True)
