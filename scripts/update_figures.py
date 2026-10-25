"""
scripts/update_figures.py
Generates enhanced, publication-quality fig1.pdf and fig2.pdf:
- fig1.pdf: Clean 2x2 factorial grid diagram with extra large, bold fonts specifically sized for IEEE single-column readability.
- fig2.pdf: False-positive rate bar chart with:
    - Vertically rotated y-axis label ("False Positive Rate (FPR)")
    - Large, legible font sizes matching IEEE single-column requirements
    - Extra left margin (ox = 200) to eliminate any possible clipping or overlap
    - Clean error bars showing exact Clopper-Pearson 95% confidence intervals
    - Distinct hatched/shaded bars with clear legend
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
    # Compact canvas 1100 x 740 with large, bold text for IEEE column scaling
    w, h = 1100, 740
    img = Image.new('RGB', (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    f_axis_main = get_font(34, bold=True)
    f_axis_sub = get_font(30, bold=True)
    f_box_title = get_font(30, bold=True)
    f_box_head = get_font(26, bold=True)
    f_box_desc = get_font(24, bold=False)
    f_box_sub = get_font(22, bold=False)
    f_note = get_font(23, bold=False)
    
    # Regional axis header (Top)
    draw.text((410, 15), "Regional Axis (\u03c1)", fill=(0, 0, 0), font=f_axis_main)
    draw.text((230, 62), "Standard English", fill=(0, 51, 102), font=f_axis_sub)
    draw.text((680, 62), "Indian English", fill=(0, 51, 102), font=f_axis_sub)
    
    # Temporal axis header (Left)
    draw.text((15, 220), "Temporal\nAxis (\u03c4)", fill=(0, 0, 0), font=f_axis_main)
    draw.text((20, 375), "Contemp.", fill=(0, 51, 102), font=f_axis_sub)
    draw.text((20, 545), "Historical", fill=(0, 51, 102), font=f_axis_sub)
    
    # 2x2 Boxes
    box_w, box_h = 430, 235
    x1, y1 = 190, 115
    x2, y2 = 645, 115
    row2_y = 380
    
    # C1 (Baseline)
    draw.rectangle([x1, y1, x1 + box_w, y1 + box_h], outline=(0, 0, 0), width=3, fill=(245, 248, 254))
    draw.text((x1 + 20, y1 + 18), "C1: Baseline", fill=(0, 51, 102), font=f_box_title)
    draw.text((x1 + 20, y1 + 65), "Contemporary Standard", fill=(0, 0, 0), font=f_box_head)
    draw.text((x1 + 20, y1 + 108), "In-distribution training & eval", fill=(50, 50, 50), font=f_box_desc)
    draw.text((x1 + 20, y1 + 148), "Reference for paired McNemar", fill=(70, 70, 70), font=f_box_desc)
    draw.text((x1 + 20, y1 + 190), "(\u03c4 = Contemp., \u03c1 = Std.)", fill=(100, 100, 100), font=f_box_sub)
    
    # C3 (Indian English)
    draw.rectangle([x2, y1, x2 + box_w, y1 + box_h], outline=(0, 0, 0), width=3, fill=(245, 248, 254))
    draw.text((x2 + 20, y1 + 18), "C3: Regional Shift", fill=(0, 51, 102), font=f_box_title)
    draw.text((x2 + 20, y1 + 65), "Colloquial Indian English", fill=(0, 0, 0), font=f_box_head)
    draw.text((x2 + 20, y1 + 108), "Regional syntax & discourse", fill=(50, 50, 50), font=f_box_desc)
    draw.text((x2 + 20, y1 + 148), "66.4% in-vocab token coverage", fill=(70, 70, 70), font=f_box_desc)
    draw.text((x2 + 20, y1 + 190), "(\u03c4 = Contemp., \u03c1 = Reg.)", fill=(100, 100, 100), font=f_box_sub)
    
    # C2 (Victorian)
    draw.rectangle([x1, row2_y, x1 + box_w, row2_y + box_h], outline=(0, 0, 0), width=3, fill=(245, 248, 254))
    draw.text((x1 + 20, row2_y + 18), "C2: Diachronic Shift", fill=(0, 51, 102), font=f_box_title)
    draw.text((x1 + 20, row2_y + 65), "Victorian Formal Register", fill=(0, 0, 0), font=f_box_head)
    draw.text((x1 + 20, row2_y + 108), "19th-century archaic syntax", fill=(50, 50, 50), font=f_box_desc)
    draw.text((x1 + 20, row2_y + 148), "54.4% in-vocab token coverage", fill=(70, 70, 70), font=f_box_desc)
    draw.text((x1 + 20, row2_y + 190), "(\u03c4 = Hist., \u03c1 = Std.)", fill=(100, 100, 100), font=f_box_sub)
    
    # C4 (Combined)
    draw.rectangle([x2, row2_y, x2 + box_w, row2_y + box_h], outline=(0, 0, 0), width=3, fill=(245, 248, 254))
    draw.text((x2 + 20, row2_y + 18), "C4: Dual Combined Shift", fill=(0, 51, 102), font=f_box_title)
    draw.text((x2 + 20, row2_y + 65), "Colonial Administrative", fill=(0, 0, 0), font=f_box_head)
    draw.text((x2 + 20, row2_y + 108), "Joint diachronic & regional", fill=(50, 50, 50), font=f_box_desc)
    draw.text((x2 + 20, row2_y + 148), "45.2% in-vocab token coverage", fill=(70, 70, 70), font=f_box_desc)
    draw.text((x2 + 20, row2_y + 190), "(\u03c4 = Hist., \u03c1 = Reg.)", fill=(100, 100, 100), font=f_box_sub)
    
    # Bottom control notes
    draw.text((190, 645), "Fixed labels y \u2208 {0, 1}; Controls: Cos-Sim \u2265 0.70, Length Ratio [0.70, 2.50]", fill=(40, 40, 40), font=f_note)
    draw.text((190, 680), "Interaction contrast: FPR(C4) - FPR(C2) - FPR(C3) + FPR(C1)", fill=(80, 80, 80), font=f_note)
    
    for d in ['paper', 'paper/overleaf_package']:
        img.save(os.path.join(d, 'fig1.pdf'), 'PDF', resolution=300.0)
    print("Generated enhanced fig1.pdf with large, bold fonts")

def make_fig2_pdf():
    w, h = 1500, 950
    img = Image.new('RGB', (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    f_axis = get_font(28, bold=True)
    f_tick = get_font(24, bold=False)
    f_label = get_font(24, bold=True)
    f_legend = get_font(24, bold=False)
    
    ox, oy = 200, 750
    cw, ch = 1200, 580
    
    # Y-axis gridlines and ticks (0.0 to 1.0)
    for i in range(6):
        val = i * 0.2
        y = oy - int(i * (ch / 5))
        draw.line([ox, y, ox + cw, y], fill=(225, 225, 225), width=2)
        draw.text((ox - 75, y - 16), f"{val:.1f}", fill=(0, 0, 0), font=f_tick)
        
    # Draw rotated Y-axis label cleanly
    lbl_text = "False Positive Rate (FPR) on 10 Benign Prompts"
    lbl_font = f_axis
    bbox = draw.textbbox((0, 0), lbl_text, font=lbl_font)
    txt_w = bbox[2] - bbox[0] + 10
    txt_h = bbox[3] - bbox[1] + 10
    
    txt_img = Image.new('RGBA', (txt_w, txt_h), (255, 255, 255, 0))
    txt_draw = ImageDraw.Draw(txt_img)
    txt_draw.text((5, 5), lbl_text, fill=(0, 0, 0), font=lbl_font)
    rotated_txt = txt_img.rotate(90, expand=True, resample=Image.BICUBIC)
    
    lbl_x = 40
    lbl_y = oy - ch // 2 - rotated_txt.height // 2
    img.paste(rotated_txt, (lbl_x, lbl_y), rotated_txt)
    
    # Models and FPRs with Clopper-Pearson bounds
    # Note: Named 'Char n-gram + Ridge' consistently!
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
        ("Char n-gram\n+ Ridge", [
            (0.0, 0.0, 0.31), (0.5, 0.19, 0.81), (0.3, 0.07, 0.65), (0.8, 0.44, 0.97)
        ])
    ]
    
    fills = [(255, 255, 255), (200, 210, 225), (120, 140, 165), (45, 55, 70)]
    
    gw = cw / 4
    bw = 46
    bgap = 10
    
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
                draw.line([bar_center_x, y_err_low, bar_center_x, y_err_high], fill=(0, 0, 0), width=3)
                draw.line([bar_center_x - 10, y_err_low, bar_center_x + 10, y_err_low], fill=(0, 0, 0), width=3)
                draw.line([bar_center_x - 10, y_err_high, bar_center_x + 10, y_err_high], fill=(0, 0, 0), width=3)
                
        # Model label below axis
        lines = m_label.split("\n")
        for l_idx, line in enumerate(lines):
            l_bbox = draw.textbbox((0, 0), line, font=f_label)
            l_w = l_bbox[2] - l_bbox[0]
            draw.text((g_center - l_w // 2, oy + 25 + l_idx * 34), line, fill=(0, 0, 0), font=f_label)
        
    # Main Axes
    draw.line([ox, oy, ox + cw, oy], fill=(0, 0, 0), width=3)
    draw.line([ox, oy, ox, oy - ch], fill=(0, 0, 0), width=3)
    
    # Legend
    leg_x = 780
    leg_y = 50
    labels = ["C1: Baseline", "C2: Victorian", "C3: Indian Eng.", "C4: Combined"]
    for i in range(4):
        lx = leg_x + (i % 2) * 290
        ly = leg_y + (i // 2) * 45
        draw.rectangle([lx, ly, lx + 36, ly + 28], fill=fills[i], outline=(0, 0, 0), width=2)
        draw.text((lx + 46, ly - 2), labels[i], fill=(0, 0, 0), font=f_legend)
        
    for d in ['paper', 'paper/overleaf_package']:
        img.save(os.path.join(d, 'fig2.pdf'), 'PDF', resolution=300.0)
    print("Generated enhanced fig2.pdf")

if __name__ == '__main__':
    make_fig1_pdf()
    make_fig2_pdf()
