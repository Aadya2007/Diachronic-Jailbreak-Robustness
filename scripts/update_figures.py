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

FONT_SYMBOL = 'C:/Windows/Fonts/seguisym.ttf'
SYMBOL_CHARS = set('\u2208\u2265\u2212')

def draw_text(draw, xy, text, fill, size, bold=False):
    """Draw text, using Segoe UI Symbol for math glyphs the base font may lack."""
    x, y = xy
    base = get_font(size, bold)
    try:
        sym = ImageFont.truetype(FONT_SYMBOL, size)
    except Exception:
        sym = base
    run, run_sym = '', None
    def flush():
        nonlocal x, run
        if run:
            f = sym if run_sym else base
            draw.text((x, y), run, fill=fill, font=f)
            x += draw.textlength(run, font=f)
            run = ''
    for ch in text:
        is_sym = ch in SYMBOL_CHARS
        if run and is_sym != run_sym:
            flush()
        run_sym = is_sym
        run += ch
    flush()

def make_fig1_pdf():
    # 1100 x 700 canvas; text is kept short so fonts can be large when scaled to one IEEE column
    w, h = 1100, 700
    img = Image.new('RGB', (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    navy, black = (0, 51, 102), (0, 0, 0)

    # Axis headers
    draw_text(draw, (400, 8), "Regional axis (\u03c1)", black, 38, True)
    draw_text(draw, (225, 58), "Standard", navy, 34, True)
    draw_text(draw, (720, 58), "Indian English", navy, 34, True)
    draw_text(draw, (12, 8), "Temporal axis (\u03c4)", black, 36, True)
    draw_text(draw, (12, 195), "Contemp.", navy, 32, True)
    draw_text(draw, (12, 420), "Historical", navy, 32, True)

    box_w, box_h = 430, 205
    xs = [190, 645]
    ys = [110, 335]
    boxes = [
        (0, 0, "C1: Baseline", "Contemporary std.", "(\u03c4 = Contemp., \u03c1 = Std.)", "100% in-vocab tokens"),
        (1, 0, "C3: Regional", "Colloquial Indian", "(\u03c4 = Contemp., \u03c1 = Reg.)", "66.4% in-vocab tokens"),
        (0, 1, "C2: Historical", "Victorian formal", "(\u03c4 = Hist., \u03c1 = Std.)", "54.4% in-vocab tokens"),
        (1, 1, "C4: Combined", "Colonial administrative", "(\u03c4 = Hist., \u03c1 = Reg.)", "45.2% in-vocab tokens"),
    ]
    for cx, cy, title, reg, taurho, cov in boxes:
        x, y = xs[cx], ys[cy]
        draw.rectangle([x, y, x + box_w, y + box_h], outline=black, width=3, fill=(245, 248, 254))
        draw_text(draw, (x + 18, y + 12), title, navy, 38, True)
        draw_text(draw, (x + 18, y + 66), reg, black, 32, True)
        draw_text(draw, (x + 18, y + 114), taurho, (50, 50, 50), 30)
        draw_text(draw, (x + 18, y + 156), cov, (70, 70, 70), 30)

    # Bottom notes
    draw_text(draw, (190, 570), "Labels fixed: y \u2208 {0, 1}", (40, 40, 40), 32)
    draw_text(draw, (190, 612), "Targets: cos-sim \u2265 0.70, length ratio [0.70, 2.50]", (40, 40, 40), 32)
    draw_text(draw, (190, 654), "Interaction: FPR(C4) \u2212 FPR(C2) \u2212 FPR(C3) + FPR(C1)", (60, 60, 60), 30)

    for d in ['paper', 'paper/overleaf_package']:
        img.save(os.path.join(d, 'fig1.pdf'), 'PDF', resolution=300.0)
    img.save('paper/figures/fig1_preview_check.png')
    print("Generated fig1.pdf with larger fonts")

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
