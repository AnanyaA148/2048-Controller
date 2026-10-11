using TMPro;
using UnityEngine;

public class BoardManager : MonoBehaviour
{
    // The game state. GameManager reads and writes this directly.
    public int[,] board = new int[4, 4];

    [Header("16 tiles, row by row, top-left first")]
    public Tile[] tiles = new Tile[16];

    ColorManager[] colors;

    void Awake()
    {
        colors = new ColorManager[tiles.Length];

        for (int i = 0; i < tiles.Length; i++)
        {
            // Find the number text automatically if it wasn't assigned on the Tile
            if (tiles[i].numberText == null)
                tiles[i].numberText = tiles[i].GetComponentInChildren<TextMeshProUGUI>();

            // Find (or add) the ColorManager on the same object as the Tile
            colors[i] = tiles[i].GetComponent<ColorManager>();
            if (colors[i] == null)
                colors[i] = tiles[i].gameObject.AddComponent<ColorManager>();
        }
    }

    public void UpdateUI()
    {
        for (int r = 0; r < 4; r++)
        {
            for (int c = 0; c < 4; c++)
            {
                int i = r * 4 + c;
                int value = board[r, c];

                tiles[i].SetValue(value);
                tiles[i].numberText.color = value <= 4 ? new Color(0.47f, 0.43f, 0.40f) : Color.white;
                colors[i].SetColor(value);
            }
        }
    }
}