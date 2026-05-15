from __future__ import annotations

import sqlite3
from collections import deque
from pathlib import Path

RELATIONS = {
    "belongs_to", "located_in", "inherited_by", "similar_to", "derived_from",
    "part_of_group", "relates_to_activity", "discussed_in", "user_interested_in",
    "user_participated", "user_posted_about", "region_adjacent",
}
ENTITY_TYPES = {"ICHItem", "Category", "Region", "Inheritor", "Activity", "Post", "User"}
DB_PATH = Path(__file__).resolve().parents[2] / "knowledge_graph.db"

SEED_ENTITIES = [
    ("苏绣", "ICHItem"), ("蜀绣", "ICHItem"), ("湘绣", "ICHItem"), ("粤绣", "ICHItem"), ("昆曲", "ICHItem"),
    ("京剧", "ICHItem"), ("越剧", "ICHItem"), ("黄梅戏", "ICHItem"), ("古琴艺术", "ICHItem"), ("南京云锦", "ICHItem"),
    ("宜兴紫砂陶制作技艺", "ICHItem"), ("龙泉青瓷烧制技艺", "ICHItem"), ("端午节", "ICHItem"), ("中医针灸", "ICHItem"),
    ("木版年画", "ICHItem"), ("皮影戏", "ICHItem"), ("中国剪纸", "ICHItem"), ("中国书法", "ICHItem"), ("太极拳", "ICHItem"),
    ("二十四节气", "ICHItem"), ("传统技艺", "Category"), ("传统戏剧", "Category"), ("传统音乐", "Category"), ("民俗", "Category"),
    ("传统美术", "Category"), ("传统体育", "Category"), ("传统医药", "Category"), ("四大名绣", "Category"), ("江南戏曲", "Category"),
    ("宫廷织造", "Category"), ("蚕桑文化", "Category"), ("农耕文明", "Category"), ("岁时节令", "Category"), ("江苏", "Region"),
    ("四川", "Region"), ("湖南", "Region"), ("广东", "Region"), ("北京", "Region"), ("浙江", "Region"), ("湖北", "Region"),
    ("安徽", "Region"), ("陕西", "Region"), ("苏绣代表性传承人", "Inheritor"), ("蜀绣代表性传承人", "Inheritor"),
    ("昆曲代表性传承人", "Inheritor"), ("古琴艺术代表性传承人", "Inheritor"), ("云锦代表性传承人", "Inheritor"),
    ("苏绣体验工坊", "Activity"), ("昆曲青春版展演", "Activity"), ("皮影戏亲子体验", "Activity"), ("二十四节气主题讲座", "Activity"),
    ("非遗周末市集", "Activity"), ("苏绣和蜀绣有什么区别", "Post"), ("第一次看昆曲是什么体验", "Post"),
    ("周末带孩子体验皮影戏", "Post"), ("云锦适合做文创吗", "Post"), ("用户A", "User"), ("用户B", "User"), ("用户C", "User"),
]

SEED_TRIPLES = [
    ("苏绣", "belongs_to", "传统技艺", 0.96), ("蜀绣", "belongs_to", "传统技艺", 0.95), ("湘绣", "belongs_to", "传统技艺", 0.95),
    ("粤绣", "belongs_to", "传统技艺", 0.94), ("昆曲", "belongs_to", "传统戏剧", 0.97), ("京剧", "belongs_to", "传统戏剧", 0.97),
    ("越剧", "belongs_to", "传统戏剧", 0.95), ("黄梅戏", "belongs_to", "传统戏剧", 0.94), ("古琴艺术", "belongs_to", "传统音乐", 0.96),
    ("南京云锦", "belongs_to", "传统技艺", 0.96), ("宜兴紫砂陶制作技艺", "belongs_to", "传统技艺", 0.95), ("龙泉青瓷烧制技艺", "belongs_to", "传统技艺", 0.95),
    ("端午节", "belongs_to", "民俗", 0.96), ("中医针灸", "belongs_to", "传统医药", 0.97), ("木版年画", "belongs_to", "传统美术", 0.95),
    ("皮影戏", "belongs_to", "传统戏剧", 0.95), ("中国剪纸", "belongs_to", "传统美术", 0.95), ("中国书法", "belongs_to", "传统美术", 0.94),
    ("太极拳", "belongs_to", "传统体育", 0.96), ("二十四节气", "belongs_to", "民俗", 0.95),
    ("苏绣", "located_in", "江苏", 0.97), ("蜀绣", "located_in", "四川", 0.97), ("湘绣", "located_in", "湖南", 0.97),
    ("粤绣", "located_in", "广东", 0.97), ("昆曲", "located_in", "江苏", 0.93), ("京剧", "located_in", "北京", 0.96),
    ("越剧", "located_in", "浙江", 0.96), ("黄梅戏", "located_in", "安徽", 0.95), ("古琴艺术", "located_in", "江苏", 0.90),
    ("南京云锦", "located_in", "江苏", 0.97), ("龙泉青瓷烧制技艺", "located_in", "浙江", 0.97), ("皮影戏", "located_in", "陕西", 0.70),
    ("苏绣", "inherited_by", "苏绣代表性传承人", 0.92), ("蜀绣", "inherited_by", "蜀绣代表性传承人", 0.92), ("昆曲", "inherited_by", "昆曲代表性传承人", 0.91),
    ("古琴艺术", "inherited_by", "古琴艺术代表性传承人", 0.91), ("南京云锦", "inherited_by", "云锦代表性传承人", 0.91),
    ("苏绣", "similar_to", "蜀绣", 0.91), ("苏绣", "similar_to", "湘绣", 0.88), ("蜀绣", "similar_to", "粤绣", 0.86),
    ("昆曲", "similar_to", "越剧", 0.82), ("京剧", "similar_to", "黄梅戏", 0.78), ("中国剪纸", "similar_to", "木版年画", 0.76),
    ("南京云锦", "similar_to", "苏绣", 0.74), ("龙泉青瓷烧制技艺", "similar_to", "宜兴紫砂陶制作技艺", 0.73),
    ("苏绣", "derived_from", "蚕桑文化", 0.82), ("蜀绣", "derived_from", "蚕桑文化", 0.80), ("南京云锦", "derived_from", "宫廷织造", 0.90),
    ("端午节", "derived_from", "农耕文明", 0.85), ("二十四节气", "derived_from", "农耕文明", 0.89),
    ("苏绣", "part_of_group", "四大名绣", 0.95), ("蜀绣", "part_of_group", "四大名绣", 0.95), ("湘绣", "part_of_group", "四大名绣", 0.95),
    ("粤绣", "part_of_group", "四大名绣", 0.95), ("昆曲", "part_of_group", "江南戏曲", 0.82), ("越剧", "part_of_group", "江南戏曲", 0.80),
    ("端午节", "part_of_group", "岁时节令", 0.88), ("二十四节气", "part_of_group", "岁时节令", 0.91),
    ("苏绣", "relates_to_activity", "苏绣体验工坊", 0.90), ("昆曲", "relates_to_activity", "昆曲青春版展演", 0.93),
    ("皮影戏", "relates_to_activity", "皮影戏亲子体验", 0.92), ("二十四节气", "relates_to_activity", "二十四节气主题讲座", 0.89),
    ("南京云锦", "relates_to_activity", "非遗周末市集", 0.75), ("苏绣", "discussed_in", "苏绣和蜀绣有什么区别", 0.87),
    ("蜀绣", "discussed_in", "苏绣和蜀绣有什么区别", 0.87), ("昆曲", "discussed_in", "第一次看昆曲是什么体验", 0.90),
    ("皮影戏", "discussed_in", "周末带孩子体验皮影戏", 0.91), ("南京云锦", "discussed_in", "云锦适合做文创吗", 0.86),
    ("用户A", "user_interested_in", "苏绣", 0.83), ("用户A", "user_interested_in", "南京云锦", 0.76), ("用户B", "user_interested_in", "昆曲", 0.82),
    ("用户B", "user_interested_in", "古琴艺术", 0.80), ("用户C", "user_interested_in", "皮影戏", 0.84),
    ("用户A", "user_participated", "苏绣体验工坊", 0.88), ("用户B", "user_participated", "昆曲青春版展演", 0.88), ("用户C", "user_participated", "皮影戏亲子体验", 0.88),
    ("用户A", "user_posted_about", "云锦适合做文创吗", 0.74), ("用户B", "user_posted_about", "第一次看昆曲是什么体验", 0.77), ("用户C", "user_posted_about", "周末带孩子体验皮影戏", 0.79),
    ("江苏", "region_adjacent", "浙江", 0.71), ("江苏", "region_adjacent", "安徽", 0.68), ("安徽", "region_adjacent", "湖北", 0.66),
    ("浙江", "region_adjacent", "安徽", 0.65), ("湖南", "region_adjacent", "湖北", 0.64), ("四川", "region_adjacent", "湖北", 0.58),
]


class KnowledgeGraphService:
    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()
        self._ensure_seed_data()
        # P0#4: 邻接表+实体映射缓存，避免每次请求重建
        self._entity_map_cache: dict[str, str] | None = None
        self._neighbors_cache: dict | None = None
        # 新增查询结果缓存（P1优化）
        self._similar_cache: dict[str, dict] = {}
        self._expand_cache: dict[tuple[str, int, int], dict] = {}
        self._path_cache: dict[tuple[str, str], dict] = {}

    def _invalidate_cache(self):
        """清空缓存，在数据变更（添加实体/三元组）后调用"""
        self._entity_map_cache = None
        self._neighbors_cache = None
        # 清空查询结果缓存
        self._similar_cache = {}
        self._expand_cache = {}
        self._path_cache = {}

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self):
        with self._connect() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS entities(name TEXT PRIMARY KEY, entity_type TEXT NOT NULL)")
            conn.execute("CREATE TABLE IF NOT EXISTS triples(id INTEGER PRIMARY KEY AUTOINCREMENT, subject TEXT NOT NULL, relation TEXT NOT NULL, object TEXT NOT NULL, weight REAL NOT NULL DEFAULT 1.0)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_triples_subject ON triples(subject)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_triples_object ON triples(object)")
            conn.commit()

    def _ensure_seed_data(self):
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(1) c FROM triples").fetchone()
            if row and row["c"]:
                return
            for name, entity_type in SEED_ENTITIES:
                conn.execute("INSERT OR REPLACE INTO entities(name,entity_type) VALUES(?,?)", (name, entity_type))
            for subject, relation, obj, weight in SEED_TRIPLES:
                conn.execute("INSERT INTO triples(subject,relation,object,weight) VALUES(?,?,?,?)", (subject, relation, obj, weight))
            conn.commit()

    def _entity_map(self):
        if self._entity_map_cache is not None:
            return self._entity_map_cache
        with self._connect() as conn:
            rows = conn.execute("SELECT name,entity_type FROM entities").fetchall()
        self._entity_map_cache = {row["name"]: row["entity_type"] for row in rows}
        return self._entity_map_cache

    def _triples(self):
        with self._connect() as conn:
            return conn.execute("SELECT subject,relation,object,weight FROM triples").fetchall()

    def _neighbors(self):
        if self._neighbors_cache is not None:
            return self._neighbors_cache
        graph = {}
        for row in self._triples():
            graph.setdefault(row["subject"], []).append({"next": row["object"], "relation": row["relation"], "weight": float(row["weight"]), "direction": "forward"})
            graph.setdefault(row["object"], []).append({"next": row["subject"], "relation": row["relation"], "weight": float(row["weight"]), "direction": "reverse"})
        self._neighbors_cache = graph
        return graph

    def shortest_path(self, from_entity: str, to_entity: str):
        entity_map = self._entity_map()
        if from_entity not in entity_map or to_entity not in entity_map:
            return {"from": from_entity, "to": to_entity, "distance": -1, "path": [], "message": "实体不存在"}
        graph, queue, visited, prev = self._neighbors(), deque([from_entity]), {from_entity}, {}
        while queue:
            current = queue.popleft()
            if current == to_entity:
                break
            for edge in graph.get(current, []):
                nxt = edge["next"]
                if nxt in visited:
                    continue
                visited.add(nxt)
                prev[nxt] = (current, edge)
                queue.append(nxt)
        if to_entity not in visited:
            return {"from": from_entity, "to": to_entity, "distance": -1, "path": [], "message": "未找到可达路径"}
        nodes, edges, cursor = [to_entity], [], to_entity
        while cursor != from_entity:
            parent, edge = prev[cursor]
            nodes.append(parent)
            edges.append(edge)
            cursor = parent
        nodes.reverse()
        edges.reverse()
        path = []
        for idx, node in enumerate(nodes):
            path.append({"entity": node, "entity_type": entity_map.get(node, "Unknown")})
            if idx < len(edges):
                path.append({"relation": edges[idx]["relation"], "weight": edges[idx]["weight"], "direction": edges[idx]["direction"]})
        return {"from": from_entity, "to": to_entity, "distance": len(edges), "path": path, "message": "success"}

    def similar_entities(self, entity: str, limit: int = 8):
        # 检查缓存
        cache_key = (entity, limit)
        if cache_key in self._similar_cache:
            return self._similar_cache[cache_key]
        
        entity_map = self._entity_map()
        if entity not in entity_map:
            result = {"entity": entity, "items": [], "message": "实体不存在"}
            self._similar_cache[cache_key] = result
            return result
            
        with self._connect() as conn:
            rows = conn.execute("SELECT subject,object,weight FROM triples WHERE relation='similar_to' AND (subject=? OR object=?) ORDER BY weight DESC", (entity, entity)).fetchall()
        items = []
        for row in rows:
            other = row["object"] if row["subject"] == entity else row["subject"]
            items.append({"entity": other, "entity_type": entity_map.get(other, "Unknown"), "similarity": float(row["weight"]), "relation": "similar_to"})
        
        result = {"entity": entity, "items": items[:limit], "message": "success"}
        self._similar_cache[cache_key] = result
        return result

    def expand_recommendations(self, entity: str, depth: int = 2, limit: int = 12):
        # 检查缓存
        max_depth = max(1, min(int(depth or 2), 4))
        cache_key = (entity, max_depth, limit)
        if cache_key in self._expand_cache:
            return self._expand_cache[cache_key]
        
        entity_map = self._entity_map()
        if entity not in entity_map:
            result = {"entity": entity, "depth": max_depth, "items": [], "message": "实体不存在"}
            self._expand_cache[cache_key] = result
            return result
            
        graph, queue, seen, results = self._neighbors(), deque([(entity, 0, [entity], [], 1.0)]), {entity: 0}, []
        while queue:
            current, current_depth, nodes, relations, score = queue.popleft()
            if current_depth >= max_depth:
                continue
            for edge in graph.get(current, []):
                nxt, next_depth = edge["next"], current_depth + 1
                next_score = round(score * edge["weight"], 4)
                if seen.get(nxt, 99) < next_depth:
                    continue
                seen[nxt] = next_depth
                next_nodes, next_relations = nodes + [nxt], relations + [edge["relation"]]
                queue.append((nxt, next_depth, next_nodes, next_relations, next_score))
                if nxt != entity:
                    results.append({"entity": nxt, "entity_type": entity_map.get(nxt, "Unknown"), "depth": next_depth, "score": round(next_score / next_depth, 4), "path": next_nodes, "relations": next_relations, "reason": " → ".join(next_relations)})
        best = {}
        for item in results:
            if item["entity"] not in best or item["score"] > best[item["entity"]]["score"]:
                best[item["entity"]] = item
        items = sorted(best.values(), key=lambda item: (item["depth"], -item["score"], item["entity"]))[:limit]
        
        result = {"entity": entity, "depth": max_depth, "items": items, "message": "success"}
        self._expand_cache[cache_key] = result
        return result


kg_service = KnowledgeGraphService()
