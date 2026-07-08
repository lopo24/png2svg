from flask import Flask, request, send_file, render_template
import cv2
import numpy as np
import svgwrite
import os
import uuid

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def png_to_svg(input_path, output_path, color="#C8C4B4"):
    img = cv2.imread(input_path)
    if img is None:
        return False

    height, width = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    binary = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=15,
        C=-10
    )

    contours, hierarchy = cv2.findContours(binary, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_TC89_KCOS)

    dwg = svgwrite.Drawing(output_path, size=(f"{width}px", f"{height}px"))
    dwg.viewbox(0, 0, width, height)

    for i, contour in enumerate(contours):
        if cv2.contourArea(contour) < 10:
            continue
        points = contour.reshape(-1, 2)
        if len(points) < 2:
            continue
        is_hole = hierarchy[0][i][3] != -1
        fill_color = "none" if is_hole else color
        path_data = f"M {points[0][0]} {points[0][1]}"
        for point in points[1:]:
            path_data += f" L {point[0]} {point[1]}"
        path_data += " Z"
        dwg.add(dwg.path(d=path_data, fill=fill_color, stroke="none"))

    dwg.save()
    return True

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/convert", methods=["POST"])
def convert():
    if "file" not in request.files:
        return "Nenhum ficheiro enviado", 400

    file = request.files["file"]
    color = request.form.get("color", "#C8C4B4")

    unique = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_FOLDER, f"{unique}.png")
    output_path = os.path.join(UPLOAD_FOLDER, f"{unique}.svg")

    file.save(input_path)

    success = png_to_svg(input_path, output_path, color)

    if not success:
        return "Erro ao converter", 500

    return send_file(output_path, as_attachment=True, download_name="design.svg")

if __name__ == "__main__":
    app.run(debug=True)