using UnityEngine;
using TMPro;

public class Tile : MonoBehaviour
{
    public int value;
    public TextMeshProUGUI numberText;

    public void SetValue(int v)
    {
        value = v;

        if(value == 0)
            numberText.text = "";
        else
            numberText.text = v.ToString();
    }
}