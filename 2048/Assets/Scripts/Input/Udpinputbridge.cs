using System;
using System.Collections.Concurrent;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;

public enum ControlMode { Keyboard, Hand, Eyes, PiButtons }

/// <summary>
/// Bridges the three external input scripts to the game.
/// Listens on one UDP port per script, but only forwards moves from the mode the
/// player picked in the start menu, calling InputManager.TriggerMove for each one.
/// </summary>
public class UdpInputBridge : MonoBehaviour
{
    [SerializeField] InputManager inputManager;

    [Header("UDP ports (must match the Python scripts)")]
    [SerializeField] int handPort = 5005;   // hand_tracking_2048.py
    [SerializeField] int eyePort = 5006;    // eye_tracking_2048.py
    [SerializeField] int piPort = 5007;     // pi_buttons_2048.py

    [Header("Options")]
    [Tooltip("Keep the arrow keys / WASD working as a backup after a mode is picked")]
    [SerializeField] bool keyboardAlsoWorks = true;

    public ControlMode CurrentMode { get; private set; } = ControlMode.Keyboard;
    public bool InputActive { get; private set; }

    PortListener handListener, eyeListener, piListener;
    void Awake()
    {
       Application.runInBackground = true;
    }

    void OnEnable()
    {
        handListener = PortListener.Create(handPort, "Hand");
        eyeListener = PortListener.Create(eyePort, "Eyes");
        piListener = PortListener.Create(piPort, "Pi");
    }

    void OnDisable()
    {
        handListener?.Dispose();
        eyeListener?.Dispose();
        piListener?.Dispose();
    }

    void Start() => PauseInput(); // nothing moves until a mode is chosen in the menu

    /// <summary>Called by the menu when the player picks an input.</summary>
    public void SelectMode(ControlMode mode)
    {
        CurrentMode = mode;
        InputActive = true;

        handListener?.Clear();
        eyeListener?.Clear();
        piListener?.Clear();

        // InputManager.Update is what reads the keyboard, so enabling/disabling it toggles the keyboard.
        inputManager.enabled = keyboardAlsoWorks || mode == ControlMode.Keyboard;
    }

    /// <summary>Called while the menu is open: block every input.</summary>
    public void PauseInput()
    {
        InputActive = false;
        inputManager.enabled = false;
    }

    void Update()
    {
        // Always drain every queue so old messages never pile up, but only forward the chosen one.
        Forward(handListener, ControlMode.Hand);
        Forward(eyeListener, ControlMode.Eyes);
        Forward(piListener, ControlMode.PiButtons);
    }

    void Forward(PortListener listener, ControlMode mode)
    {
        if (listener == null) return;

        while (listener.TryDequeue(out MoveDirection dir))
        {
            if (InputActive && CurrentMode == mode)
                inputManager.TriggerMove(dir);
        }
    }

    // ------------------------------------------------------------------

    /// <summary>One background thread listening on one UDP port.</summary>
    class PortListener : IDisposable
    {
        readonly UdpClient client;
        readonly Thread thread;
        readonly ConcurrentQueue<MoveDirection> queue = new ConcurrentQueue<MoveDirection>();
        volatile bool running = true;

        PortListener(int port)
        {
            client = new UdpClient(port);
            thread = new Thread(Listen) { IsBackground = true };
            thread.Start();
        }

        public static PortListener Create(int port, string label)
        {
            try { return new PortListener(port); }
            catch (SocketException e)
            {
                Debug.LogError($"UdpInputBridge: could not listen on port {port} ({label}). Is something else using it? {e.Message}");
                return null;
            }
        }

        void Listen()
        {
            var endpoint = new IPEndPoint(IPAddress.Any, 0);
            while (running)
            {
                try
                {
                    byte[] data = client.Receive(ref endpoint);
                    string msg = Encoding.UTF8.GetString(data).Trim().ToLowerInvariant();

                    switch (msg)
                    {
                        case "up":    queue.Enqueue(MoveDirection.Up);    break;
                        case "down":  queue.Enqueue(MoveDirection.Down);  break;
                        case "left":  queue.Enqueue(MoveDirection.Left);  break;
                        case "right": queue.Enqueue(MoveDirection.Right); break;
                    }
                }
                catch (SocketException) { if (!running) break; }
                catch (ObjectDisposedException) { break; }
            }
        }

        public bool TryDequeue(out MoveDirection dir) => queue.TryDequeue(out dir);

        public void Clear() { while (queue.TryDequeue(out _)) { } }

        public void Dispose()
        {
            running = false;
            client.Close();
        }
    }
}