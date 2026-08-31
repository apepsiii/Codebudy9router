# 🎨 UGC Content Generator API Integration

**Use Case:** Generate UGC-style photos & video storyboards untuk affiliate products

---

## 🏗️ ARCHITECTURE

```
Affiliate Tracker (Python)
    ↓
Product Info + Content Type
    ↓
Prompt Generator (Python)
    ↓
HTTP Request → Your Backend API
    ↓
Image Generation (Stable Diffusion/Flux/etc)
    ↓
Response: Image URLs
    ↓
Save to Database + Return to user
```

---

## 📋 YANG KAMU BUTUHKAN DI BACKEND

### 1. API Endpoint Specifications

#### **POST /api/generate-ugc-photo**

**Request:**
```json
{
  "product_name": "Sandal Baim Unisex",
  "product_category": "Fashion",
  "product_description": "Sandal unisex stylish dari bahan EVA",
  "scene_type": "lifestyle_indoor | lifestyle_outdoor | product_flat_lay | unboxing | on_feet | comparison | review_setup",
  "style": "ugc_casual | ugc_professional | influencer_style | authentic_raw",
  "aspect_ratio": "1:1 | 9:16 | 16:9 | 4:5",
  "num_images": 1,
  "seed": 42,
  "negative_prompt": "professional studio, commercial, watermark"
}
```

**Response:**
```json
{
  "status": "success",
  "job_id": "uuid-xxxxx",
  "images": [
    {
      "url": "https://your-cdn.com/images/abc123.jpg",
      "prompt": "full prompt that was used",
      "seed": 42,
      "width": 1024,
      "height": 1024
    }
  ],
  "generation_time_ms": 2500
}
```

#### **POST /api/generate-video-storyboard**

**Request:**
```json
{
  "product_name": "Sandal Baim Unisex",
  "content_type": "tiktok_reel | instagram_reel | youtube_short",
  "video_concept": "POV unboxing | lifestyle_day_in_life | product_review",
  "duration_seconds": 30,
  "num_scenes": 5,
  "style": "ugc_casual"
}
```

**Response:**
```json
{
  "status": "success",
  "storyboard_id": "uuid-yyyyy",
  "scenes": [
    {
      "scene_number": 1,
      "timestamp": "0-3s",
      "description": "Close-up hands opening Shopee package",
      "image_url": "https://your-cdn.com/scenes/scene1.jpg",
      "prompt_used": "...",
      "shot_type": "close_up",
      "text_overlay": "Wait for it... 😱"
    },
    {
      "scene_number": 2,
      "timestamp": "3-8s",
      "description": "First look at sandals, genuine reaction",
      "image_url": "https://your-cdn.com/scenes/scene2.jpg",
      "prompt_used": "...",
      "shot_type": "medium_shot",
      "text_overlay": "28rb?! 🤯"
    }
  ],
  "audio_suggestion": "trending_upbeat_sound",
  "hashtags": ["#SandalBaim", "#UnboxingTikTok"]
}
```

---

## 🔑 AUTHENTICATION

### Option 1: API Key (Simple) ⭐ RECOMMENDED untuk MVP
```
Authorization: Bearer YOUR_API_KEY
```

### Option 2: OAuth2 (Advanced)
```
Authorization: Bearer {access_token}
```

### Option 3: HMAC Signature (Secure)
```
X-Signature: sha256(secret + timestamp + payload)
X-Timestamp: 1693456789
```

---

## 📤 PYTHON CLIENT (Yang Aku Sediakan)

### Config File Format:

```yaml
# ~/.hermes/ugc_api_config.yaml

api_base_url: "https://your-backend.com"
api_key: "your_api_key_here"
timeout_seconds: 60

# Default settings
defaults:
  scene_type: "lifestyle_indoor"
  style: "ugc_casual"
  aspect_ratio: "1:1"
  num_images: 1
```

### Python Client Usage:

```python
from ugc_generator_client import UGCGeneratorClient

# Initialize client
client = UGCGeneratorClient(
    api_base_url="https://your-backend.com",
    api_key="your_api_key"
)

# Generate single photo
photo = client.generate_ugc_photo(
    product_name="Sandal Baim Unisex",
    product_category="Fashion",
    product_description="Sandal stylish dari EVA, anti-slip, 10 warna",
    scene_type="lifestyle_indoor",
    style="ugc_casual",
    aspect_ratio="4:5"
)

print(f"Image URL: {photo['images'][0]['url']}")

# Generate video storyboard
storyboard = client.generate_video_storyboard(
    product_name="Sandal Baim Unisex",
    content_type="tiktok_reel",
    video_concept="POV unboxing",
    duration_seconds=30,
    num_scenes=5
)

for scene in storyboard['scenes']:
    print(f"Scene {scene['scene_number']}: {scene['description']}")
    print(f"  Image: {scene['image_url']}")
```

---

## 🎨 PROMPT TEMPLATES

### UGC Photo Prompts:

```python
SCENE_PROMPTS = {
    "lifestyle_indoor": """
A casual, authentic UGC style photo of {product_name}.
Scene: Natural home setting, person using/wearing the product.
Lighting: Soft natural window light, warm tone.
Angle: Slightly from above, smartphone camera perspective.
Quality: iPhone photo, authentic feel, NOT professional studio.
Details: {product_description}
Style: Real person, lived-in space, comfortable.
Negative: watermark, studio lighting, commercial
    """,
    
    "unboxing": """
Unboxing moment of {product_name}, UGC style.
Scene: Hands opening package on table/bed.
Items: Package, product visible.
Lighting: Natural indoor light.
Angle: Top-down, smartphone perspective.
Emotion: Excitement, genuine reaction.
Quality: Smartphone camera, real moment.
Negative: professional photography, studio setup
    """,
    
    "on_feet": """
{product_name} being worn, UGC style.
Scene: Real environment - sidewalk, home.
Subject: Natural pose, product in focus.
Lighting: Natural daylight.
Angle: Low angle, person taking photo of own feet.
Quality: Smartphone camera, authentic.
Negative: professional model, studio
    """,
    
    "flat_lay": """
Flat lay of {product_name}, Instagram UGC.
Scene: Clean surface - bed, table, marble.
Composition: Product centered, minimal props.
Lighting: Natural overhead, soft shadows.
Angle: Directly above, grid composition.
Quality: Smartphone, planned but casual.
Negative: commercial product shot, perfect lighting
    """
}
```

### Video Storyboard Prompts:

```python
VIDEO_CONCEPTS = {
    "pov_unboxing": [
        {
            "timestamp": "0-3s",
            "description": "Close-up hands opening package",
            "shot_type": "close_up",
            "prompt": "POV hands opening Shopee package, {product_name} visible inside"
        },
        {
            "timestamp": "3-8s",
            "description": "First reaction",
            "shot_type": "medium_shot",
            "prompt": "Person's genuine reaction seeing {product_name}, surprised face"
        },
        {
            "timestamp": "8-15s",
            "description": "Product showcase",
            "shot_type": "close_up",
            "prompt": "Hands holding {product_name}, showing key features"
        },
        {
            "timestamp": "15-25s",
            "description": "In-use demo",
            "shot_type": "medium_shot",
            "prompt": "Person wearing/using {product_name}, natural setting"
        },
        {
            "timestamp": "25-30s",
            "description": "CTA moment",
            "shot_type": "medium_shot",
            "prompt": "Person pointing to {product_name}, happy expression"
        }
    ]
}
```

---

## 🚀 BACKEND TECH STACK RECOMMENDATIONS

### Option A: FastAPI (Python) ⭐ RECOMMENDED

**Pros:**
- Same language as frontend (easy sharing code)
- Fast, async
- Auto API docs (Swagger)
- Type validation (Pydantic)
- Easy ML model integration

**Cons:**
- Python GIL (use workers for scaling)

**Example:**
```python
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import uuid

app = FastAPI()

class UGCPhotoRequest(BaseModel):
    product_name: str
    product_category: str
    product_description: str
    scene_type: str = "lifestyle_indoor"
    style: str = "ugc_casual"
    aspect_ratio: str = "1:1"
    num_images: int = 1

@app.post("/api/generate-ugc-photo")
async def generate_ugc_photo(request: UGCPhotoRequest):
    job_id = str(uuid.uuid4())
    
    # Generate image (your logic)
    image_url = await generate_image(request)
    
    return {
        "status": "success",
        "job_id": job_id,
        "images": [{
            "url": image_url,
            "prompt": build_prompt(request),
            "width": 1024,
            "height": 1024
        }]
    }
```

### Option B: Node.js + Express

**Pros:**
- Good async performance
- Large ecosystem
- Easy streaming

**Cons:**
- Less ML library support
- Type safety needs TypeScript

### Option C: Go

**Pros:**
- Very fast
- Good concurrency
- Low memory

**Cons:**
- Verbose
- Smaller ML ecosystem

---

## 🖼️ IMAGE GENERATION OPTIONS

### Option 1: Replicate API ⭐ EASIEST

**Pros:**
- No infra setup
- Pay per use
- Many models

**Cons:**
- Cost per image
- API dependency

```python
import replicate

output = replicate.run(
    "stability-ai/sdxl:xxxxx",
    input={
        "prompt": ugc_prompt,
        "negative_prompt": "studio, watermark",
        "width": 1024,
        "height": 1024
    }
)
image_url = output[0]
```

### Option 2: ComfyUI Backend

**Pros:**
- Full control
- Custom workflows
- One-time GPU cost

**Cons:**
- Need GPU server
- DevOps complexity

### Option 3: Diffusers + Own Server

**Pros:**
- Full customization
- Own models/LoRAs
- No API limits

**Cons:**
- Infrastructure management
- GPU costs

```python
from diffusers import StableDiffusionXLPipeline
import torch

pipe = StableDiffusionXLPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=torch.float16
).to("cuda")

image = pipe(
    prompt=ugc_prompt,
    negative_prompt="studio, watermark",
    num_inference_steps=30
).images[0]
```

---

## 💾 STORAGE & CDN

### Recommended Stack:

**Storage:** Cloudflare R2 / AWS S3
- Cheap
- Scalable
- Easy integration

**CDN:** Cloudflare CDN / AWS CloudFront
- Fast delivery
- Image optimization
- Cache

**Database:** PostgreSQL
- Metadata (jobs, images, users)
- API key management
- Usage tracking

**Cache/Queue:** Redis
- Job queue
- Rate limiting
- Response caching

---

## 📊 DATA FLOW

```
1. Client sends request with product info
2. Backend validates API key & quota
3. Backend builds prompt from template
4. Backend calls image generation (Replicate/ComfyUI/Own)
5. Image saved to S3/R2
6. CDN URL returned to client
7. Client saves URL to database
8. User downloads/uses image
```

---

## 🔐 SECURITY CHECKLIST

- [ ] API key authentication
- [ ] Rate limiting (10 requests/min per key)
- [ ] Input validation (prevent prompt injection)
- [ ] HTTPS only
- [ ] CORS configuration
- [ ] Request size limits
- [ ] Timeout handling
- [ ] Error message sanitization (no internal info leak)

---

## 📈 MONITORING

### Metrics to Track:

```python
- requests_total (counter)
- generation_time_seconds (histogram)
- errors_total (counter)
- active_jobs (gauge)
- cost_per_image_usd (gauge)
- queue_depth (gauge)
```

### Logging:

```json
{
  "timestamp": "2026-08-31T05:50:33.210Z",
  "request_id": "uuid",
  "api_key_masked": "sk_***abc",
  "endpoint": "/api/generate-ugc-photo",
  "product_name": "Sandal Baim",
  "scene_type": "unboxing",
  "generation_time_ms": 2500,
  "status": "success",
  "cost_usd": 0.02
}
```

---

## 🧪 TESTING

### Test Request:

```bash
curl -X POST https://your-api.com/api/generate-ugc-photo \
  -H "Authorization: Bearer test_key_123" \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Sandal Baim Unisex",
    "product_category": "Fashion",
    "product_description": "Sandal EVA anti-slip",
    "scene_type": "lifestyle_indoor",
    "style": "ugc_casual",
    "aspect_ratio": "1:1",
    "num_images": 1
  }'
```

### Expected Response:

```json
{
  "status": "success",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "images": [
    {
      "url": "https://cdn.example.com/images/550e8400.jpg",
      "prompt": "A casual, authentic UGC style photo of Sandal Baim Unisex...",
      "seed": 42,
      "width": 1024,
      "height": 1024
    }
  ],
  "generation_time_ms": 2456
}
```

---

## 📋 MVP CHECKLIST

### Phase 1 (Week 1) - MVP:
- [ ] FastAPI backend setup
- [ ] `/generate-ugc-photo` endpoint (sync)
- [ ] API key authentication
- [ ] Replicate API integration
- [ ] Basic prompt templates
- [ ] S3/R2 storage
- [ ] Error handling

### Phase 2 (Week 2) - Enhancement:
- [ ] Async job queue (Celery/Redis)
- [ ] `/generate-video-storyboard` endpoint
- [ ] Rate limiting
- [ ] Usage tracking
- [ ] Monitoring/logging

### Phase 3 (Week 3+) - Scale:
- [ ] Cost optimization
- [ ] Prompt caching
- [ ] Custom LoRA models
- [ ] Batch processing
- [ ] Webhook callbacks

---

## 💰 COST ESTIMATION

### Using Replicate (Pay per use):
- SDXL generation: ~$0.002-0.01 per image
- 1000 images/month: $2-10/month

### Own GPU Server:
- GPU instance (A10G): ~$0.50-1.00/hour
- 24/7: ~$360-720/month
- Break-even: ~36,000 images/month

**Recommendation:** Start with Replicate, switch to own server at scale.

---

## 🎯 INTEGRATION POINTS

### From Hermes Side (Aku handle):

1. **Product info extraction** from database
2. **Prompt generation** based on content type
3. **API calls** to your backend
4. **Image URL storage** in database
5. **CLI commands** untuk trigger generation
6. **Error handling & retries**

### From Your Backend (Kamu handle):

1. **API endpoints** receiving requests
2. **Authentication** validation
3. **Prompt → Image** generation
4. **Storage** (S3/R2)
5. **CDN URLs** return
6. **Rate limiting & quotas**

---

## 📞 NEXT STEPS

1. **Pilih tech stack** (FastAPI recommended)
2. **Setup image generation** (Replicate easiest)
3. **Deploy MVP** (single endpoint)
4. **Share API endpoint + key** with me
5. **Aku integrate** dari Hermes side
6. **Test & iterate**

---

Mau aku buatin:
- [ ] Python client library (lengkap)
- [ ] FastAPI backend skeleton
- [ ] Prompt templates library
- [ ] CLI tool untuk testing

Atau kamu mau fokus backend dulu, nanti kasih tau API endpoint-nya? 🚀
