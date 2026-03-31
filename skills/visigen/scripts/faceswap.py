"""
VISIGEN Face Swap Post-Processor
Swaps the generated avatar face with Rich's reference face using InsightFace.

Usage:
  python faceswap.py <source_thumbnail.png> <output.png>
  python faceswap.py <source_thumbnail.png> <output.png> --reference <path_to_ref.jpg>

Default reference: ../references/rich_reference.jpg
"""

import sys
import os
import argparse
import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis
from insightface.model_zoo import get_model

REFERENCE_PATH = os.path.join(os.path.dirname(__file__), '..', 'references', 'rich_reference.jpg')
SWAPPER_MODEL = os.path.join(os.path.dirname(__file__), '..', 'models', 'inswapper_128.onnx')


def download_swapper_model():
    """Download inswapper_128.onnx if not present."""
    model_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, 'inswapper_128.onnx')
    if not os.path.exists(model_path):
        print("Downloading face swap model (inswapper_128.onnx)...")
        import urllib.request
        url = "https://huggingface.co/deepinsight/inswapper/resolve/main/inswapper_128.onnx"
        urllib.request.urlretrieve(url, model_path)
        print(f"Model saved to {model_path}")
    return model_path


def swap_face(source_img_path, reference_img_path, output_path):
    print("Initializing face analysis...")
    app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640))

    model_path = download_swapper_model()
    print("Loading face swap model...")
    swapper = get_model(model_path, download=False, download_zip=False)

    # Load reference (source face - Rich)
    ref_img = cv2.imread(reference_img_path)
    if ref_img is None:
        print(f"ERROR: Could not load reference image: {reference_img_path}")
        sys.exit(1)
    ref_faces = app.get(ref_img)
    if not ref_faces:
        print("ERROR: No face detected in reference image.")
        sys.exit(1)
    ref_face = ref_faces[0]
    print(f"Reference face detected (confidence: {ref_face.det_score:.2f})")

    # Load target (generated thumbnail)
    target_img = cv2.imread(source_img_path)
    if target_img is None:
        print(f"ERROR: Could not load source image: {source_img_path}")
        sys.exit(1)
    target_faces = app.get(target_img)
    if not target_faces:
        print("ERROR: No face detected in source thumbnail.")
        sys.exit(1)
    print(f"Found {len(target_faces)} face(s) in thumbnail.")

    # Swap all faces in the thumbnail with Rich's face
    result = target_img.copy()
    for face in target_faces:
        result = swapper.get(result, face, ref_face, paste_back=True)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    cv2.imwrite(output_path, result)
    print(f"Face swap complete. Saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Face swap post-processor for VISIGEN thumbnails')
    parser.add_argument('source', help='Source thumbnail PNG path')
    parser.add_argument('output', help='Output PNG path')
    parser.add_argument('--reference', default=REFERENCE_PATH, help='Reference face image path')
    args = parser.parse_args()

    if not os.path.exists(args.source):
        print(f"ERROR: Source not found: {args.source}")
        sys.exit(1)
    if not os.path.exists(args.reference):
        print(f"ERROR: Reference not found: {args.reference}")
        sys.exit(1)

    swap_face(args.source, args.reference, args.output)


if __name__ == '__main__':
    main()
