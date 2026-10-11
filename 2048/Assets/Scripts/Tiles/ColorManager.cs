using UnityEngine;
using UnityEngine.UI;

public class ColorManager : MonoBehaviour
{
    // Auto-filled from the Image on the same object if left empty
    public Image tileImage;

    void Awake()
    {
        if (tileImage == null) tileImage = GetComponent<Image>();
    }

    // Call this whenever the tile value changes
    public void SetColor(int value)
    {
        if (value == 0)
        {
            tileImage.color = new Color32(205, 193, 180, 255); // empty tile
            return;
        }

        switch (value)
        {
            case 2:
                tileImage.color = new Color32(238, 228, 218, 255);
                break;
            case 4:
                tileImage.color = new Color32(237, 224, 200, 255);
                break;
            case 8:
                tileImage.color = new Color32(242, 177, 121, 255);
                break;
            case 16:
                tileImage.color = new Color32(245, 149, 99, 255);
                break;
            case 32:
                tileImage.color = new Color32(246, 124, 95, 255);
                break;
            case 64:
                tileImage.color = new Color32(246, 94, 59, 255);
                break;
            case 128:
                tileImage.color = new Color32(237, 207, 114, 255);
                break;
            case 256:
                tileImage.color = new Color32(237, 204, 97, 255);
                break;
            case 512:
                tileImage.color = new Color32(237, 200, 80, 255);
                break;
            case 1024:
                tileImage.color = new Color32(237, 197, 63, 255);
                break;
            case 2048:
                tileImage.color = new Color32(237, 194, 46, 255);
                break;
            default:
                tileImage.color = new Color32(60, 58, 50, 255); // >2048
                break;
        }
    }
}