# One-time export of CLIP ViT-B/32 (OpenAI weights, the same as open_clip 'ViT-B-32/openai') to ONNX, so /gen can embed
# text and preview frames on this container's CPU without torch (Hugging Face is not reachable from the container).
# Inputs: check.png. OUT: clip_text.onnx, clip_image.onnx, clip_tokenizer.json, check.json (reference embeddings).
import json, numpy as np, torch
from PIL import Image
from transformers import CLIPModel, CLIPTokenizerFast, CLIPImageProcessor
M = 'openai/clip-vit-base-patch32'; O = os.environ['OUT']
m = CLIPModel.from_pretrained(M).eval().requires_grad_(False); torch.set_grad_enabled(False); tok = CLIPTokenizerFast.from_pretrained(M); proc = CLIPImageProcessor.from_pretrained(M)
tok.backend_tokenizer.save(f'{O}/clip_tokenizer.json')


class Text(torch.nn.Module):
    def __init__(self): super().__init__(); self.m = m
    def forward(self, ids, mask): return self.m.text_projection(self.m.text_model(input_ids=ids, attention_mask=mask).pooler_output)


class Img(torch.nn.Module):
    def __init__(self): super().__init__(); self.m = m
    def forward(self, px): return self.m.visual_projection(self.m.vision_model(pixel_values=px).pooler_output)


t = tok(['a red tyre', 'a giant bold word'], padding='max_length', max_length=77, truncation=True, return_tensors='pt')
px = proc(images=[Image.open('check.png').convert('RGB')], return_tensors='pt')['pixel_values']
kw = dict(opset_version=17)
try: torch.onnx.export(Text(), (t['input_ids'], t['attention_mask']), f'{O}/clip_text.onnx', input_names=['input_ids', 'attention_mask'],
                       output_names=['emb'], dynamic_axes={'input_ids': {0: 'b'}, 'attention_mask': {0: 'b'}, 'emb': {0: 'b'}}, dynamo=False, **kw)
except TypeError: torch.onnx.export(Text(), (t['input_ids'], t['attention_mask']), f'{O}/clip_text.onnx', input_names=['input_ids', 'attention_mask'],
                                    output_names=['emb'], dynamic_axes={'input_ids': {0: 'b'}, 'attention_mask': {0: 'b'}, 'emb': {0: 'b'}}, **kw)
try: torch.onnx.export(Img(), (px,), f'{O}/clip_image.onnx', input_names=['pixel_values'], output_names=['emb'],
                       dynamic_axes={'pixel_values': {0: 'b'}, 'emb': {0: 'b'}}, dynamo=False, **kw)
except TypeError: torch.onnx.export(Img(), (px,), f'{O}/clip_image.onnx', input_names=['pixel_values'], output_names=['emb'],
                                    dynamic_axes={'pixel_values': {0: 'b'}, 'emb': {0: 'b'}}, **kw)
with torch.no_grad():
    json.dump(dict(texts=['a red tyre', 'a giant bold word'], text=Text()(t['input_ids'], t['attention_mask']).tolist(),
                   ids=t['input_ids'].tolist(), image=Img()(px).tolist()), open(f'{O}/check.json', 'w'))
print('exported', os.listdir(O))
