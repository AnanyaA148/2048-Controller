using UnityEngine;

public enum MoveDirection { Up, Down, Left, Right }

public class InputManager : MonoBehaviour
{
    public System.Action<MoveDirection> OnMove;

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.UpArrow)) OnMove?.Invoke(MoveDirection.Up);
        if (Input.GetKeyDown(KeyCode.DownArrow)) OnMove?.Invoke(MoveDirection.Down);
        if (Input.GetKeyDown(KeyCode.LeftArrow)) OnMove?.Invoke(MoveDirection.Left);
        if (Input.GetKeyDown(KeyCode.RightArrow)) OnMove?.Invoke(MoveDirection.Right);
    }
}