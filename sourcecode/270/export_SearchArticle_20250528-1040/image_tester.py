#image_tester.py
from PIL import Image
from io import BytesIO
import base64

with open("debug_output.png", "rb") as f:
    raw_bytes = f.read()
    print("PNG grootte (bytes):", len(raw_bytes))

# encode naar base64
b64 = base64.b64encode(raw_bytes).decode("utf-8")
print("Base64 lengte:", len(b64))

# decode opnieuw en probeer PIL
decoded = base64.b64decode(b64)
image = Image.open(BytesIO(decoded))
image.show()  # opent standaard viewer
