"""
main.py — Self-Contained Production Kaggle Kernel for ARC Prize 2026 (Version 7)
Integrates AdvancedASTSynthesizer (Sub-Graph Isomorphism & Program Synthesis) with Automatic Fallback to V6.
Runs on Kaggle's private test set and generates submission.json.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import List, Tuple, Dict, Any, Callable
import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# 1. Extractor de Objetos 2D (Flood-fill 8-conectividad)
# ─────────────────────────────────────────────────────────────────────────────

class ARCObject:
    def __init__(self, object_id: int, color: int, pixels: List[Tuple[int, int]], bbox: Tuple[int, int, int, int], area: int, centroid: Tuple[float, float], shape_signature: str):
        self.object_id = object_id
        self.color = color
        self.pixels = pixels
        self.bbox = bbox
        self.area = area
        self.centroid = centroid
        self.shape_signature = shape_signature


class ARCObjectExtractor:
    def __init__(self, background_color: int = 0):
        self.background_color = background_color

    def extract_objects(self, grid: List[List[int]]) -> List[ARCObject]:
        arr = np.array(grid, dtype=int)
        rows, cols = arr.shape
        visited = np.zeros((rows, cols), dtype=bool)
        objects = []
        obj_counter = 1

        for r in range(rows):
            for c in range(cols):
                color = int(arr[r, c])
                if color != self.background_color and not visited[r, c]:
                    pixels = self._flood_fill(arr, visited, r, c, color, rows, cols)
                    if pixels:
                        obj = self._create_arc_object(obj_counter, color, pixels)
                        objects.append(obj)
                        obj_counter += 1
        return objects

    def _flood_fill(self, arr: np.ndarray, visited: np.ndarray, r: int, c: int, color: int, rows: int, cols: int) -> List[Tuple[int, int]]:
        pixels = []
        queue = [(r, c)]
        visited[r, c] = True
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

        while queue:
            curr_r, curr_c = queue.pop(0)
            pixels.append((curr_r, curr_c))
            for dr, dc in directions:
                nr, nc = curr_r + dr, curr_c + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    if not visited[nr, nc] and arr[nr, nc] == color:
                        visited[nr, nc] = True
                        queue.append((nr, nc))
        return pixels

    def _create_arc_object(self, obj_id: int, color: int, pixels: List[Tuple[int, int]]) -> ARCObject:
        rows = [p[0] for p in pixels]
        cols = [p[1] for p in pixels]
        min_r, max_r = min(rows), max(rows)
        min_c, max_c = min(cols), max(cols)
        area = len(pixels)
        centroid = (float(np.mean(rows)), float(np.mean(cols)))
        norm_coords = sorted([(r - min_r, c - min_c) for r, c in pixels])
        signature = f"{max_r - min_r + 1}x{max_c - min_c + 1}_" + "_".join(f"{r}:{c}" for r, c in norm_coords)
        return ARCObject(obj_id, color, pixels, (min_r, min_c, max_r, max_c), area, centroid, signature)


# ─────────────────────────────────────────────────────────────────────────────
# 2. Solucionador Determinista V6 (Fallback Solver)
# ─────────────────────────────────────────────────────────────────────────────

def _gravity_down(g: np.ndarray) -> np.ndarray:
    res = np.zeros_like(g)
    for c in range(g.shape[1]):
        col = g[:, c]
        nz = col[col != 0]
        if len(nz) > 0:
            res[-len(nz):, c] = nz
    return res

def _gravity_up(g: np.ndarray) -> np.ndarray:
    res = np.zeros_like(g)
    for c in range(g.shape[1]):
        col = g[:, c]
        nz = col[col != 0]
        if len(nz) > 0:
            res[:len(nz), c] = nz
    return res

def _gravity_left(g: np.ndarray) -> np.ndarray:
    res = np.zeros_like(g)
    for r in range(g.shape[0]):
        row = g[r, :]
        nz = row[row != 0]
        if len(nz) > 0:
            res[r, :len(nz)] = nz
    return res

def _gravity_right(g: np.ndarray) -> np.ndarray:
    res = np.zeros_like(g)
    for r in range(g.shape[0]):
        row = g[r, :]
        nz = row[row != 0]
        if len(nz) > 0:
            res[r, -len(nz):] = nz
    return res

def _crop_bbox(g: np.ndarray) -> np.ndarray:
    nz = np.argwhere(g != 0)
    if len(nz) == 0:
        return g.copy()
    min_r, min_c = nz.min(axis=0)
    max_r, max_c = nz.max(axis=0)
    return g[min_r:max_r+1, min_c:max_c+1]

def _crop_largest_object(g: np.ndarray) -> np.ndarray:
    extractor = ARCObjectExtractor()
    objects = extractor.extract_objects(g.tolist())
    if not objects:
        return g.copy()
    largest_obj = max(objects, key=lambda o: o.area)
    min_r, min_c, max_r, max_c = largest_obj.bbox
    return g[min_r:max_r+1, min_c:max_c+1]

def _tile_2x2(g: np.ndarray) -> np.ndarray:
    return np.block([[g, g], [g, g]])

def _scale_2x(g: np.ndarray) -> np.ndarray:
    return np.repeat(np.repeat(g, 2, axis=0), 2, axis=1)

def _fill_holes(g: np.ndarray) -> np.ndarray:
    res = g.copy()
    rows, cols = g.shape
    visited = np.zeros((rows, cols), dtype=bool)
    queue = []
    for r in range(rows):
        for c in (0, cols - 1):
            if res[r, c] == 0 and not visited[r, c]:
                visited[r, c] = True
                queue.append((r, c))
    for c in range(cols):
        for r in (0, rows - 1):
            if res[r, c] == 0 and not visited[r, c]:
                visited[r, c] = True
                queue.append((r, c))

    while queue:
        curr_r, curr_c = queue.pop(0)
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = curr_r + dr, curr_c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                if not visited[nr, nc] and res[nr, nc] == 0:
                    visited[nr, nc] = True
                    queue.append((nr, nc))

    for r in range(rows):
        for c in range(cols):
            if res[r, c] == 0 and not visited[r, c]:
                res[r, c] = 1
    return res

def _outline(g: np.ndarray) -> np.ndarray:
    res = np.zeros_like(g)
    rows, cols = g.shape
    for r in range(rows):
        for c in range(cols):
            if g[r, c] != 0:
                is_border = False
                if r == 0 or r == rows - 1 or c == 0 or c == cols - 1:
                    is_border = True
                else:
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        if g[r+dr, c+dc] == 0:
                            is_border = True
                            break
                if is_border:
                    res[r, c] = g[r, c]
    return res

def _hollow_objects(g: np.ndarray) -> np.ndarray:
    res = g.copy()
    rows, cols = g.shape
    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            if g[r, c] != 0:
                if (g[r-1, c] == g[r, c] and g[r+1, c] == g[r, c] and
                    g[r, c-1] == g[r, c] and g[r, c+1] == g[r, c]):
                    res[r, c] = 0
    return res

def _swap_most_and_least_frequent_colors(g: np.ndarray) -> np.ndarray:
    res = g.copy()
    non_zeros = g[g != 0]
    if len(non_zeros) < 2:
        return res
    vals, counts = np.unique(non_zeros, return_counts=True)
    if len(vals) < 2:
        return res
    most_c = vals[np.argmax(counts)]
    least_c = vals[np.argmin(counts)]
    mask_most = g == most_c
    mask_least = g == least_c
    res[mask_most] = least_c
    res[mask_least] = most_c
    return res

def _connect_dots(g: np.ndarray) -> np.ndarray:
    res = g.copy()
    rows, cols = g.shape
    for r in range(rows):
        colors = {}
        for c in range(cols):
            color = g[r, c]
            if color != 0:
                if color in colors:
                    c_prev = colors[color]
                    res[r, c_prev:c+1] = color
                colors[color] = c
    for c in range(cols):
        colors = {}
        for r in range(rows):
            color = g[r, c]
            if color != 0:
                if color in colors:
                    r_prev = colors[color]
                    res[r_prev:r+1, c] = color
                colors[color] = r
    return res

def _connect_dots_diagonal(g: np.ndarray) -> np.ndarray:
    res = g.copy()
    rows, cols = g.shape
    for r in range(rows - 1):
        for c in range(cols - 1):
            color = g[r, c]
            if color != 0:
                for d in range(1, min(rows - r, cols - c)):
                    if g[r + d, c + d] == color:
                        for i in range(1, d):
                            res[r + i, c + i] = color
                        break
    return res

def _select_most_frequent_color(g: np.ndarray) -> np.ndarray:
    res = np.zeros_like(g)
    non_zeros = g[g != 0]
    if len(non_zeros) == 0:
        return res
    vals, counts = np.unique(non_zeros, return_counts=True)
    top_color = vals[np.argmax(counts)]
    res[g == top_color] = top_color
    return res

def _select_least_frequent_color(g: np.ndarray) -> np.ndarray:
    res = np.zeros_like(g)
    non_zeros = g[g != 0]
    if len(non_zeros) == 0:
        return res
    vals, counts = np.unique(non_zeros, return_counts=True)
    least_color = vals[np.argmin(counts)]
    res[g == least_color] = least_color
    return res

def _mirror_horizontal(g: np.ndarray) -> np.ndarray:
    res = g.copy()
    w = g.shape[1]
    mid = w // 2
    if w % 2 == 0:
        res[:, mid:] = np.fliplr(g[:, :mid])
    else:
        res[:, mid+1:] = np.fliplr(g[:, :mid])
    return res

def _mirror_vertical(g: np.ndarray) -> np.ndarray:
    res = g.copy()
    h = g.shape[0]
    mid = h // 2
    if h % 2 == 0:
        res[mid:, :] = np.flipud(g[:mid, :])
    else:
        res[mid+1:, :] = np.flipud(g[:mid, :])
    return res

def _shift_down_1(g: np.ndarray) -> np.ndarray:
    return np.roll(g, 1, axis=0)

def _shift_up_1(g: np.ndarray) -> np.ndarray:
    return np.roll(g, -1, axis=0)

def _shift_right_1(g: np.ndarray) -> np.ndarray:
    return np.roll(g, 1, axis=1)

def _shift_left_1(g: np.ndarray) -> np.ndarray:
    return np.roll(g, -1, axis=1)

def _invert_colors(g: np.ndarray) -> np.ndarray:
    res = g.copy()
    mask = res != 0
    res[mask] = (10 - res[mask]) % 10
    return res


class ARCHypothesis:
    def __init__(self, name: str, transform_fn: Callable[[np.ndarray], np.ndarray]):
        self.name = name
        self.transform_fn = transform_fn

    def apply(self, grid: List[List[int]]) -> List[List[int]]:
        arr = np.array(grid, dtype=int)
        res = self.transform_fn(arr)
        return res.tolist()


class ARCSATSolver:
    def __init__(self):
        self.hypotheses = self._build_hypothesis_space()
        self.extractor = ARCObjectExtractor()

    def _build_hypothesis_space(self) -> List[ARCHypothesis]:
        return [
            ARCHypothesis("IDENTITY", lambda g: g.copy()),
            ARCHypothesis("ROTATE_90", lambda g: np.rot90(g, -1)),
            ARCHypothesis("ROTATE_180", lambda g: np.rot90(g, 2)),
            ARCHypothesis("ROTATE_270", lambda g: np.rot90(g, 1)),
            ARCHypothesis("FLIP_H", lambda g: np.fliplr(g)),
            ARCHypothesis("FLIP_V", lambda g: np.flipud(g)),
            ARCHypothesis("TRANSPOSE", lambda g: g.T),
            ARCHypothesis("GRAVITY_DOWN", _gravity_down),
            ARCHypothesis("GRAVITY_UP", _gravity_up),
            ARCHypothesis("GRAVITY_LEFT", _gravity_left),
            ARCHypothesis("GRAVITY_RIGHT", _gravity_right),
            ARCHypothesis("CROP_BBOX", _crop_bbox),
            ARCHypothesis("CROP_LARGEST", _crop_largest_object),
            ARCHypothesis("TILE_2X2", _tile_2x2),
            ARCHypothesis("SCALE_2X", _scale_2x),
            ARCHypothesis("FILL_HOLES", _fill_holes),
            ARCHypothesis("OUTLINE", _outline),
            ARCHypothesis("HOLLOW_OBJECTS", _hollow_objects),
            ARCHypothesis("SWAP_MOST_LEAST_FREQ", _swap_most_and_least_frequent_colors),
            ARCHypothesis("CONNECT_DOTS", _connect_dots),
            ARCHypothesis("CONNECT_DOTS_DIAG", _connect_dots_diagonal),
            ARCHypothesis("SELECT_MOST_FREQUENT", _select_most_frequent_color),
            ARCHypothesis("SELECT_LEAST_FREQUENT", _select_least_frequent_color),
            ARCHypothesis("MIRROR_H", _mirror_horizontal),
            ARCHypothesis("MIRROR_V", _mirror_vertical),
            ARCHypothesis("SHIFT_DOWN_1", _shift_down_1),
            ARCHypothesis("SHIFT_UP_1", _shift_up_1),
            ARCHypothesis("SHIFT_RIGHT_1", _shift_right_1),
            ARCHypothesis("SHIFT_LEFT_1", _shift_left_1),
            ARCHypothesis("INVERT_COLORS", _invert_colors),
        ]

    def solve_puzzle(self, train_pairs: List[Dict[str, List[List[int]]]], test_input: List[List[int]]) -> List[List[int]]:
        for hyp in self.hypotheses:
            consistent = True
            for pair in train_pairs:
                inp = pair["input"]
                target_out = pair["output"]
                pred_out = hyp.apply(inp)
                if not self._grids_equal(pred_out, target_out):
                    consistent = False
                    break
            if consistent:
                return hyp.apply(test_input)

        primitives = [h for h in self.hypotheses if h.name != "IDENTITY"]
        for h1 in primitives:
            for h2 in primitives:
                consistent = True
                for pair in train_pairs:
                    inp = pair["input"]
                    target_out = pair["output"]
                    try:
                        pred_out = h2.apply(h1.apply(inp))
                        if not self._grids_equal(pred_out, target_out):
                            consistent = False
                            break
                    except Exception:
                        consistent = False
                        break
                if consistent:
                    return h2.apply(h1.apply(test_input))

        for h1 in primitives[:12]:
            for h2 in primitives[:12]:
                for h3 in primitives[:12]:
                    consistent = True
                    for pair in train_pairs:
                        inp = pair["input"]
                        target_out = pair["output"]
                        try:
                            pred_out = h3.apply(h2.apply(h1.apply(inp)))
                            if not self._grids_equal(pred_out, target_out):
                                consistent = False
                                break
                        except Exception:
                            consistent = False
                            break
                    if consistent:
                        return h3.apply(h2.apply(h1.apply(test_input)))

        color_map = self._deduce_color_map(train_pairs)
        if color_map is not None:
            return self._apply_color_map(test_input, color_map)

        return test_input

    def _deduce_color_map(self, train_pairs: List[Dict[str, List[List[int]]]]) -> Dict[int, int] | None:
        cmap: Dict[int, int] = {}
        for pair in train_pairs:
            inp = np.array(pair["input"])
            out = np.array(pair["output"])
            if inp.shape != out.shape:
                return None
            for r in range(inp.shape[0]):
                for c in range(inp.shape[1]):
                    c_in = int(inp[r, c])
                    c_out = int(out[r, c])
                    if c_in in cmap and cmap[c_in] != c_out:
                        return None
                    cmap[c_in] = c_out
        return cmap if cmap else None

    def _apply_color_map(self, grid: List[List[int]], cmap: Dict[int, int]) -> List[List[int]]:
        arr = np.array(grid, dtype=int)
        res = np.zeros_like(arr)
        for r in range(arr.shape[0]):
            for c in range(arr.shape[1]):
                c_in = int(arr[r, c])
                res[r, c] = cmap.get(c_in, c_in)
        return res.tolist()

    def _grids_equal(self, g1: List[List[int]], g2: List[List[int]]) -> bool:
        if len(g1) != len(g2):
            return False
        if len(g1) > 0 and len(g1[0]) != len(g2[0]):
            return False
        return np.array_equal(np.array(g1), np.array(g2))


# ─────────────────────────────────────────────────────────────────────────────
# 3. Sintetizador Avanzado AST e Isomorfismo de Sub-Grafos con Fallback V6
# ─────────────────────────────────────────────────────────────────────────────

class SubgraphCondition:
    def __init__(self, name: str, predicate: Callable[[ARCObject, np.ndarray], bool]):
        self.name = name
        self.predicate = predicate

class SubgraphAction:
    def __init__(self, name: str, action_fn: Callable[[ARCObject, np.ndarray], None]):
        self.name = name
        self.action_fn = action_fn

class ASTProgram:
    def __init__(self, condition: SubgraphCondition, action: SubgraphAction):
        self.condition = condition
        self.action = action

    def execute(self, grid: List[List[int]], extractor: ARCObjectExtractor) -> List[List[int]]:
        arr = np.array(grid, dtype=int)
        res = arr.copy()
        objects = extractor.extract_objects(grid)
        for obj in objects:
            if self.condition.predicate(obj, arr):
                self.action.action_fn(obj, res)
        return res.tolist()

class AdvancedASTSynthesizer:
    def __init__(self):
        self.extractor = ARCObjectExtractor()
        self.fallback_solver = ARCSATSolver()
        self.conditions = self._build_conditions()
        self.actions = self._build_actions()

    def _build_conditions(self) -> List[SubgraphCondition]:
        conds = []
        for c in range(1, 10):
            conds.append(SubgraphCondition(f"COLOR_IS_{c}", lambda obj, g, color=c: obj.color == color))
        conds.append(SubgraphCondition("IS_LARGEST_AREA", self._is_largest_area))
        conds.append(SubgraphCondition("IS_SMALLEST_AREA", self._is_smallest_area))
        return conds

    def _is_largest_area(self, obj: ARCObject, g: np.ndarray) -> bool:
        objs = self.extractor.extract_objects(g.tolist())
        if not objs:
            return False
        max_a = max(o.area for o in objs)
        return obj.area == max_a

    def _is_smallest_area(self, obj: ARCObject, g: np.ndarray) -> bool:
        objs = self.extractor.extract_objects(g.tolist())
        if not objs:
            return False
        min_a = min(o.area for o in objs)
        return obj.area == min_a

    def _build_actions(self) -> List[SubgraphAction]:
        acts = []
        for target_c in range(0, 10):
            acts.append(SubgraphAction(f"SET_COLOR_{target_c}", lambda obj, g, tc=target_c: self._recolor_object(obj, g, tc)))
        return acts

    def _recolor_object(self, obj: ARCObject, grid_arr: np.ndarray, target_color: int):
        for r, c in obj.pixels:
            grid_arr[r, c] = target_color

    def solve_puzzle_advanced(self, train_pairs: List[Dict[str, List[List[int]]]], test_input: List[List[int]]) -> List[List[int]]:
        for cond in self.conditions:
            for act in self.actions:
                prog = ASTProgram(cond, act)
                consistent = True
                for pair in train_pairs:
                    inp = pair["input"]
                    target_out = pair["output"]
                    try:
                        pred_out = prog.execute(inp, self.extractor)
                        if not np.array_equal(np.array(pred_out), np.array(target_out)):
                            consistent = False
                            break
                    except Exception:
                        consistent = False
                        break

                if consistent:
                    return prog.execute(test_input, self.extractor)

        return self.fallback_solver.solve_puzzle(train_pairs, test_input)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Punto de Entrada Principal para el Entorno Kaggle
# ─────────────────────────────────────────────────────────────────────────────

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    print("=== ARC PRIZE 2026 — ONTOLOGY ENGINE KERNEL EXECUTION (V7 - AST & FALLBACK SAFE) ===")
    synthesizer = AdvancedASTSynthesizer()

    input_dirs = [
        Path("/kaggle/input/arc-prize-2026-arc-agi-3"),
        Path("/kaggle/input/arc-prize-2026"),
        Path("/kaggle/input/arc-agi"),
    ]

    target_dir = None
    for d in input_dirs:
        if d.exists():
            target_dir = d
            break

    submission_data = {}

    if target_dir is not None:
        print(f"Cargando dataset desde: {target_dir}")
        test_json_file = target_dir / "arc-agi_test_challenges.json"
        if not test_json_file.exists():
            test_json_file = target_dir / "test.json"

        if test_json_file.exists():
            with open(test_json_file, "r") as f:
                challenges = json.load(f)
            print(f"Desafíos de test cargados: {len(challenges)}")
            for task_id, task_data in challenges.items():
                train_pairs = task_data.get("train", [])
                test_inputs = task_data.get("test", [])
                attempts = []
                for test_item in test_inputs:
                    inp = test_item["input"]
                    pred = synthesizer.solve_puzzle_advanced(train_pairs, inp)
                    attempts.append({"attempt_1": pred, "attempt_2": pred})
                submission_data[task_id] = attempts
        else:
            for task_file in target_dir.glob("*.json"):
                task_id = task_file.stem
                with open(task_file, "r") as f:
                    task_data = json.load(f)
                train_pairs = task_data.get("train", [])
                test_inputs = task_data.get("test", [])
                attempts = []
                for test_item in test_inputs:
                    inp = test_item["input"]
                    pred = synthesizer.solve_puzzle_advanced(train_pairs, inp)
                    attempts.append({"attempt_1": pred, "attempt_2": pred})
                submission_data[task_id] = attempts
    else:
        print("Entorno de prueba local detectado. Generando submission de demostración...")
        submission_data["demo_task"] = [{"attempt_1": [[0]], "attempt_2": [[0]]}]

    output_json = Path("submission.json")
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(submission_data, f)
    print(f"✓ submission.json generado exitosamente con {len(submission_data)} tareas.")

    # Generar submission.parquet obligatorio para Kaggle
    output_parquet = Path("submission.parquet")
    rows = []
    for task_id, attempts in submission_data.items():
        rows.append({
            "id": str(task_id),
            "output": json.dumps(attempts),
            "attempt_1": json.dumps(attempts[0]["attempt_1"]) if attempts else "[]",
            "attempt_2": json.dumps(attempts[0]["attempt_2"]) if attempts else "[]"
        })
    try:
        import pandas as pd
        df = pd.DataFrame(rows)
        df.to_parquet(output_parquet)
        print(f"✓ submission.parquet generado exitosamente ({len(df)} filas).")
    except Exception as e:
        print(f"[WARN] Error exportando parquet con pandas: {e}")
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
            table = pa.Table.from_pylist(rows)
            pq.write_table(table, output_parquet)
            print("✓ submission.parquet generado exitosamente mediante PyArrow.")
        except Exception as ex:
            print(f"[ERROR] No se pudo generar Parquet: {ex}")

if __name__ == "__main__":
    main()
