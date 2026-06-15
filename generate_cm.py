import numpy as np
import matplotlib.pyplot as plt

# Using the exact mathematical metrics from your paper:
# Total: 1500 images (750 Real, 750 Fake)
# Accuracy = 96.67%
# Precision = 94.87%
# Recall = 98.67%
# True Positive (Fake detected as Fake): 740
# False Negative (Fake missed as Real): 10
# False Positive (Real mislabeled as Fake): 40
# True Negative (Real correctly labeled as Real): 710

cm = np.array([[710, 40], 
               [10, 740]])

fig, ax = plt.subplots(figsize=(8, 6))
cax = ax.matshow(cm, cmap='Blues')
plt.title('Hybrid Model Confusion Matrix\n(Accuracy: 96.67%)', pad=20, weight='bold', fontsize=16)

# Add a color bar
fig.colorbar(cax)

# Add the numbers inside the squares
for i in range(2):
    for j in range(2):
        c = cm[j, i]
        ax.text(i, j, str(c), va='center', ha='center', size=22,
                color='white' if c > 350 else 'black', weight='bold')

# Style the axes
ax.set_xticks([0, 1])
ax.set_yticks([0, 1])
ax.set_xticklabels(['Real', 'Fake'], fontsize=14, weight='bold')
ax.set_yticklabels(['Real', 'Fake'], fontsize=14, weight='bold')
ax.xaxis.set_ticks_position('bottom')

plt.xlabel('Predicted Label', weight='bold', fontsize=14, labelpad=15)
plt.ylabel('True Label', weight='bold', fontsize=14, labelpad=15)

plt.tight_layout()

# Save the image in high resolution for the IEEE paper
plt.savefig('confusion_matrix_v3.png', dpi=300, bbox_inches='tight')
print("✅ Success! Your high-resolution confusion matrix was saved as 'confusion_matrix_v3.png'.")
