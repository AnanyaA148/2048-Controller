using System;
using UnityEngine;

public enum MoveDirection { Up, Down, Left, Right }

public class InputManager : MonoBehaviour
{
    // GameManager subscribes to this in Start()
    public event Action<MoveDirection> OnMove;

    void Update()
    {
        // Keyboard for now. Later, the cvzone / Raspberry Pi input
        // can just call TriggerMove(...) from another script.
        if (Input.GetKeyDown(KeyCode.UpArrow) || Input.GetKeyDown(KeyCode.W)) TriggerMove(MoveDirection.Up);
        else if (Input.GetKeyDown(KeyCode.DownArrow) || Input.GetKeyDown(KeyCode.S)) TriggerMove(MoveDirection.Down);
        else if (Input.GetKeyDown(KeyCode.LeftArrow) || Input.GetKeyDown(KeyCode.A)) TriggerMove(MoveDirection.Left);
        else if (Input.GetKeyDown(KeyCode.RightArrow) || Input.GetKeyDown(KeyCode.D)) TriggerMove(MoveDirection.Right);
    }

    public void TriggerMove(MoveDirection dir)
    {
        OnMove?.Invoke(dir);
    }
}