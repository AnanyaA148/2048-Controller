using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// The "pick your input" screen shown when the game starts.
/// Put this on an always-active object (NOT on the panel itself, which gets hidden).
/// Press M during the game to bring the menu back and switch input.
/// </summary>
public class InputMenu : MonoBehaviour
{
    [SerializeField] GameObject menuPanel;
    [SerializeField] UdpInputBridge bridge;

    [Header("Buttons")]
    [SerializeField] Button handButton;
    [SerializeField] Button eyeButton;
    [SerializeField] Button piButton;
    [SerializeField] Button keyboardButton; // optional, handy for testing

    void Start()
    {
        handButton.onClick.AddListener(() => Choose(ControlMode.Hand));
        eyeButton.onClick.AddListener(() => Choose(ControlMode.Eyes));
        piButton.onClick.AddListener(() => Choose(ControlMode.PiButtons));
        if (keyboardButton != null)
            keyboardButton.onClick.AddListener(() => Choose(ControlMode.Keyboard));

        Show();
    }

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.M)) Show();
    }

    void Choose(ControlMode mode)
    {
        bridge.SelectMode(mode);
        menuPanel.SetActive(false);
    }

    void Show()
    {
        bridge.PauseInput();
        menuPanel.SetActive(true);
    }
}