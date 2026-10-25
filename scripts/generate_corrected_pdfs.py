"""
generate_corrected_pdfs.py
Generates clean, readable fig1.pdf and fig2.pdf matching the exact pilot figures:
- fig1.pdf: Clean 2x2 factorial grid (Standard vs Regional x Contemporary vs Historical)
- fig2.pdf: False-positive rate bar chart with 95% Clopper-Pearson confidence intervals
"""

import os
from PIL import Image, ImageDraw, ImageFont

FONT_REGULAR = 'C:/Windows/Fonts/segoeui.ttf'
FONT_BOLD = 'C:/Windows/Fonts/segoeuib.ttf'

def get_font(size, bold=False):
    f_path = FONT_BOLD if bold else FONT_REGULAR
    try:
        return ImageFont.truetype(f_path, size)
    except:
        return ImageFont.load_default()

def make_fig1_pdf():
    # 2x2 factorial grid diagram matching screenshot on Page 2
    w, h = 1200, 750
    img = Image.new('RGB', (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    f_axis = get_font(26, bold=True)
    f_title = get_font(22, bold=True)
    f_body = get_font(20, bold=False)
    f_foot = get_font(18, bold=False)
    
    # Axis headers
    draw.text((500, 30), "Regional axis rho", fill=(0, 0, 0), font=f_axis)
    draw.text((360, 75), "Standard", fill=(0, 0, 0), font=f_axis)
    draw.text((780, 75), "Regional", fill=(0, 0, 0), font=f_axis)
    
    draw.text((40, 240), "Temporal\naxis tau", fill=(0, 0, 0), font=f_axis)
    draw.text((40, 420), "Contemp.", fill=(0, 0, 0), font=f_body)
    draw.text((40, 580), "Historical", fill=(0, 0, 0), font=f_body)
    
    # 2x2 Boxes
    box_w, box_h = 380, 220
    x1, y1 = 240, 130
    x2, y2 = 660, 130
    row2_y = 390
    
    # C1 (Baseline)
    draw.rectangle([x1, y1, x1 + box_w, y1 + box_h], outline=(0, 0, 0), width=3, fill=(245, 247, 250))
    draw.text((x1 + 30, y1 + 30), "C1", fill=(0, 0, 0), font=f_axis)
    draw.text((x1 + 30, y1 + 80), "Baseline", fill=(0, 0, 0), font=f_title)
    draw.text((x1 + 30, y1 + 115), "contemporary", fill=(0, 0, 0), font=f_body)
    draw.text((x1 + 30, y1 + 145), "standard English", fill=(0, 0, 0), font=f_body)
    
    # C3 (Indian English)
    draw.rectangle([x2, y1, x2 + box_w, y1 + box_h], outline=(0, 0, 0), width=3, fill=(245, 247, 250))
    draw.text((x2 + 30, y1 + 30), "C3", fill=(0, 0, 0), font=f_axis)
    draw.text((x2 + 30, y1 + 80), "Indian English", fill=(0, 0, 0), font=f_title)
    draw.text((x2 + 30, y1 + 115), "(contemporary)", fill=(0, 0, 0), font=f_body)
    
    # C2 (Victorian)
    draw.rectangle([x1, row2_y, x1 + box_w, row2_y + box_h], outline=(0, 0, 0), width=3, fill=(245, 247, 250))
    draw.text((x1 + 30, row2_y + 30), "C2", fill=(0, 0, 0), font=f_axis)
    draw.text((x1 + 30, row2_y + 80), "Victorian register", fill=(0, 0, 0), font=f_title)
    draw.text((x1 + 30, row2_y + 115), "(standard)", fill=(0, 0, 0), font=f_body)
    
    # C4 (Combined)
    draw.rectangle([x2, row2_y, x2 + box_w, row2_y + box_h], outline=(0, 0, 0), width=3, fill=(245, 247, 250))
    draw.text((x2 + 30, row2_y + 30), "C4", fill=(0, 0, 0), font=f_axis)
    draw.text((x2 + 30, row2_y + 80), "Colonial", fill=(0, 0, 0), font=f_title)
    draw.text((x2 + 30, row2_y + 115), "administrative", fill=(0, 0, 0), font=f_body)
    draw.text((x2 + 30, row2_y + 145), "(combined)", fill=(0, 0, 0), font=f_body)
    
    # Footer caption inside figure
    draw.text((240, 650), "Same labels y; controls: cos-sim >= 0.70, length ratio [0.70, 2.50]", fill=(60, 60, 60), font=f_foot)
    
    for d in ['paper', 'paper/overleaf_package']:
        img.save(os.path.join(d, 'fig1.pdf'), 'PDF', resolution=300.0)
    print("Generated fig1.pdf")

def make_fig2_pdf():
    # Bar chart matching screenshot on Page 5 with Clopper-Pearson error bars
    w, h = 1400, 900
    img = Image.new('RGB', (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    f_axis = get_font(24, bold=True)
    f_tick = get_font(20, bold=False)
    f_label = get_font(20, bold=True)
    f_legend = get_font(20, bold=False)
    
    ox, oy = 140, 720
    cw, ch = 1180, 560
    
    # Y-axis ticks (0.0 to 1.0)
    for i in range(6):
        val = i * 0.2
        y = oy - int(i * (ch / 5))
        draw.line([ox, y, ox + cw, y], fill=(230, 230, 230), width=1)
        draw.text((ox - 65, y - 12), f"{val:.1f}", fill=(0, 0, 0), font=f_tick)
        
    draw.text((25, 450), "FPR on 10 benign prompts", fill=(0, 0, 0), font=f_axis)
    
    # Models and FPRs with Clopper-Pearson bounds
    # C1=0.0 [0, 0.31]
    # Word LogReg: C2=1.0 [0.69, 1.0], C3=1.0 [0.69, 1.0], C4=1.0 [0.69, 1.0]
    # Word LinSVC: C2=0.5 [0.19, 0.81], C3=0.2 [0.03, 0.56], C4=0.8 [0.44, 0.97]
    # Char LogReg: C2=0.9 [0.56, 1.0], C3=0.8 [0.44, 0.97], C4=0.9 [0.56, 1.0]
    # Char Margin: C2=0.5 [0.19, 0.81], C3=0.3 [0.07, 0.65], C4=0.8 [0.44, 0.97]
    
    model_data = [
        ("Word TF-IDF\n+ LogReg", [
            (0.0, 0.0, 0.31), (1.0, 0.69, 1.0), (1.0, 0.69, 1.0), (1.0, 0.69, 1.0)
        ]),
        ("Word TF-IDF\n+ LinearSVC", [
            (0.0, 0.0, 0.31), (0.5, 0.19, 0.81), (0.2, 0.03, 0.56), (0.8, 0.44, 0.97)
        ]),
        ("Char n-gram\n+ LogReg", [
            (0.0, 0.0, 0.31), (0.9, 0.56, 1.0), (0.8, 0.44, 0.97), (0.9, 0.56, 1.0)
        ]),
        ("Char n-gram\n+ Margin", [
            (0.0, 0.0, 0.31), (0.5, 0.19, 0.81), (0.3, 0.07, 0.65), (0.8, 0.44, 0.97)
        ])
    ]
    
    # Colors/hatching matching IEEE grayscale/textures
    # C1: White, C2: Diagonal hatch / light gray, C3: Medium gray, C4: Dark gray
    fills = [(255, 255, 255), (210, 215, 225), (140, 150, 165), (50, 55, 65)]
    outlines = [(0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)]
    
    gw = cw / 4
    bw = 42
    bgap = 8
    
    for m_idx, (m_label, conds) in enumerate(model_data):
        g_center = ox + m_idx * gw + gw / 2
        start_x = g_center - (4 * bw + 3 * bgap) / 2
        
        for c_idx, (val, ci_low, ci_high) in enumerate(conds):
            bx = start_x + c_idx * (bw + bgap)
            bh = int(val * ch)
            by = oy - bh
            
            # Bar
            draw.rectangle([bx, by, bx + bw, oy], fill=fills[c_idx], outline=(0, 0, 0), width=2)
            
            # Error bar
            if val > 0:
                y_err_low = oy - int(ci_low * ch)
                y_err_high = oy - int(ci_high * ch)
                bar_center_x = bx + bw // 2
                draw.line([bar_center_x, y_err_low, bar_center_x, y_err_high], fill=(0, 0, 0), width=2)
                draw.line([bar_center_x - 8, y_err_low, bar_center_x + 8, y_err_low], fill=(0, 0, 0), width=2)
                draw.line([bar_center_x - 8, y_err_high, bar_center_x + 8, y_err_high], fill=(0, 0, 0), width=2)
                
        # Model label
        lines = m_label.split("\n")
        draw.text((g_center - 70, oy + 25), lines[0], fill=(0, 0, 0), font=f_label)
        draw.text((g_center - 50, oy + 55), lines[1], fill=(0, 0, 0), font=f_label)
        
    # Axes
    draw.line([ox, oy, ox + cw, oy], fill=(0, 0, 0), width=3)
    draw.line([ox, oy, ox, oy - ch], fill=(0, 0, 0), width=3)
    
    # Legend
    leg_x = 750
    leg_y = 60
    labels = ["C1", "C2", "C3", "C4"]
    for i in range(4):
        lx = leg_x + i * 110
        draw.rectangle([lx, leg_y, lx + 25, leg_y + 20], fill=fills[i], outline=(0, 0, 0), width=2)
        draw.text((lx + 32, leg_y - 2), labels[i], fill=(0, 0, 0), font=f_legend)
        
    for d in ['paper', 'paper/overleaf_package']:
        img.save(os.path.join(d, 'fig2.pdf'), 'PDF', resolution=300.0)
    print("Generated fig2.pdf")

if __name__ == '__main__':
    make_fig1_pdf()
    make_fig2_pdf()
