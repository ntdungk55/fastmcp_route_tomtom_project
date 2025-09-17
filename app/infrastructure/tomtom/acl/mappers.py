
from app.application.dto.calculate_route_dto import RoutePlan, RouteSection, RouteSummary


class TomTomMapper:
    def to_domain_route_plan(self, payload: dict) -> RoutePlan:
        routes = payload.get("routes", [])
        if not routes:
            return RoutePlan(summary=RouteSummary(0, 0), sections=[])
        r0 = routes[0]
        s = r0.get("summary", {})
        distance = int(s.get("lengthInMeters", 0))
        duration = int(s.get("travelTimeInSeconds", 0))

        sections: list[RouteSection] = []
        for sec in r0.get("sections", []) or []:
            kind = str(sec.get("sectionType") or "")
            simple = sec.get("simpleCategory")
            if simple:
                kind = f"traffic:{simple}"
            sections.append(RouteSection(kind=kind, start_index=0, end_index=0))

        return RoutePlan(summary=RouteSummary(distance, duration), sections=sections)
