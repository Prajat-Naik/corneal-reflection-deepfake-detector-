import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Define colors matching the original diagram
c_orange = '#ff8c00'
c_blue = '#1f8bce'
c_yellow = '#ffff00'
c_green = '#98fb98'
c_red = '#ff3b30'

def draw_box(ax, x, y, width, height, text, bg_color, text_color):
    # Draw rectangle centered at x,y
    rect = patches.Rectangle((x - width/2, y - height/2), width, height, 
                             linewidth=1.5, edgecolor='#555555', facecolor=bg_color, zorder=3)
    ax.add_patch(rect)
    # Add text
    ax.text(x, y, text, color=text_color, ha='center', va='center', 
            fontsize=11, fontweight='bold', zorder=4, family='sans-serif')

def draw_line(ax, x1, y1, x2, y2):
    ax.plot([x1, x2], [y1, y2], color='black', linewidth=1.5, zorder=1)

fig, ax = plt.subplots(figsize=(10, 13), dpi=300)
ax.set_xlim(0, 1)
ax.set_ylim(0.05, 1)
ax.axis('off')

# Box dimensions
w_wide = 0.40
w_med = 0.25
h = 0.055

# Coordinates
nodes = {
    'input': (0.5, 0.95, w_med, c_orange, 'white', 'Input Image'),
    'pre1': (0.5, 0.85, w_wide, c_blue, 'white', 'Preprocessing & Face detection'),
    
    'pre2': (0.25, 0.73, w_wide, c_blue, 'white', 'Face ROI Extraction'),
    'tex': (0.25, 0.63, w_wide, c_blue, 'white', 'Facial Texture Analysis'),
    'dl': (0.25, 0.53, w_wide, c_blue, 'white', 'Deep Learning Model'),
    'score1': (0.25, 0.43, w_wide, c_yellow, 'black', 'Facial Fake Score'),
    
    'eye': (0.75, 0.73, w_wide, c_blue, 'white', 'Eye Region Cropping'),
    'refl': (0.75, 0.63, w_wide, c_blue, 'white', 'Corneal Reflection Extraction'),
    'phys': (0.75, 0.53, w_wide, c_blue, 'white', 'Physics Consistency Check'),
    'score2': (0.75, 0.43, w_wide, c_yellow, 'black', 'Physics Fake Score'),
    
    'fusion': (0.5, 0.33, w_wide, c_blue, 'white', 'Fusion Engine'),
    'logic': (0.5, 0.23, w_wide, c_yellow, 'black', 'Decision Logic'),
    
    'real': (0.35, 0.13, w_med, c_green, 'black', 'Real'),
    'fake': (0.65, 0.13, w_med, c_red, 'black', 'Fake')
}

# Draw lines
# Vertical
draw_line(ax, 0.5, 0.95, 0.5, 0.85) # input to pre1
draw_line(ax, 0.25, 0.73, 0.25, 0.43) # left branch vertical
draw_line(ax, 0.75, 0.73, 0.75, 0.43) # right branch vertical
draw_line(ax, 0.5, 0.33, 0.5, 0.23) # fusion to logic

# Diagonals from pre1 to branches
draw_line(ax, 0.5, 0.85, 0.25, 0.73)
draw_line(ax, 0.5, 0.85, 0.75, 0.73)

# Diagonals from scores to fusion
draw_line(ax, 0.25, 0.43, 0.5, 0.33)
draw_line(ax, 0.75, 0.43, 0.5, 0.33)

# Diagonals from logic to real/fake
draw_line(ax, 0.5, 0.23, 0.35, 0.13)
draw_line(ax, 0.5, 0.23, 0.65, 0.13)

# Draw boxes
for k, v in nodes.items():
    draw_box(ax, v[0], v[1], v[2], h, v[5], v[3], v[4])

# Save
plt.tight_layout()
plt.savefig(r'd:\gan_detect_iris-master\arch_white.png', bbox_inches='tight', dpi=300, facecolor='white')
print("Saved perfectly to arch_white.png")
