using UnityEngine;
using System.Collections.Generic;

public class GameManager : MonoBehaviour
{
    public BoardManager boardManager;
    public InputManager inputManager;

    void Start()
    {
        inputManager.OnMove += HandleMove;
        SpawnTile();
        SpawnTile();
        boardManager.UpdateUI();
    }

    void HandleMove(MoveDirection dir)
    {
        bool moved = Slide(dir);

        if (moved)
        {
            SpawnTile();
            boardManager.UpdateUI();
        }
    }

    bool Slide(MoveDirection dir)
    {
        bool moved = false;

        for (int i = 0; i < 4; i++)
        {
            List<int> line = GetLine(i, dir);
            List<int> processed = ProcessLine(line);

            if (!AreLinesEqual(line, processed))
                moved = true;

            SetLine(i, processed, dir);
        }

        return moved;
    }

    List<int> GetLine(int index, MoveDirection dir)
    {
        List<int> line = new List<int>();

        for (int i = 0; i < 4; i++)
        {
            switch (dir)
            {
                case MoveDirection.Left:
                    line.Add(boardManager.board[index, i]);
                    break;
                case MoveDirection.Right:
                    line.Add(boardManager.board[index, 3 - i]);
                    break;
                case MoveDirection.Up:
                    line.Add(boardManager.board[i, index]);
                    break;
                case MoveDirection.Down:
                    line.Add(boardManager.board[3 - i, index]);
                    break;
            }
        }

        return line;
    }

    void SetLine(int index, List<int> line, MoveDirection dir)
    {
        for (int i = 0; i < 4; i++)
        {
            switch (dir)
            {
                case MoveDirection.Left:
                    boardManager.board[index, i] = line[i];
                    break;
                case MoveDirection.Right:
                    boardManager.board[index, 3 - i] = line[i];
                    break;
                case MoveDirection.Up:
                    boardManager.board[i, index] = line[i];
                    break;
                case MoveDirection.Down:
                    boardManager.board[3 - i, index] = line[i];
                    break;
            }
        }
    }

    List<int> ProcessLine(List<int> line)
    {
        line = line.FindAll(v => v != 0);

        for (int i = 0; i < line.Count - 1; i++)
        {
            if (line[i] == line[i + 1])
            {
                line[i] *= 2;
                line[i + 1] = 0;
            }
        }

        line = line.FindAll(v => v != 0);

        while (line.Count < 4)
            line.Add(0);

        return line;
    }

    bool AreLinesEqual(List<int> a, List<int> b)
    {
        for (int i = 0; i < 4; i++)
            if (a[i] != b[i])
                return false;

        return true;
    }

    void SpawnTile()
    {
        List<Vector2Int> empty = new List<Vector2Int>();

        for (int r = 0; r < 4; r++)
            for (int c = 0; c < 4; c++)
                if (boardManager.board[r,c] == 0)
                    empty.Add(new Vector2Int(r,c));

        if (empty.Count == 0) return;

        Vector2Int pos = empty[Random.Range(0, empty.Count)];
        boardManager.board[pos.x, pos.y] = Random.value < 0.9f ? 2 : 4;
    }
}