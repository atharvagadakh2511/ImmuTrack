from django.shortcuts import render
from .models import Facility


def facility_list(request):
    facilities = Facility.objects.all()

    district = request.GET.get("district", "").strip()
    ownership = request.GET.get("ownership", "").strip()
    facility_type = request.GET.get("facility_type", "").strip()
    search = request.GET.get("search", "").strip()

    if district:
        facilities = facilities.filter(district__iexact=district)

    if ownership:
        facilities = facilities.filter(ownership=ownership)

    if facility_type:
        facilities = facilities.filter(facility_type__icontains=facility_type)

    if search:
        facilities = facilities.filter(
            facility_name__icontains=search
        ) | facilities.filter(
            city_or_locality__icontains=search
        ) | facilities.filter(
            district__icontains=search
        )

    districts = (
        Facility.objects
        .values_list("district", flat=True)
        .distinct()
        .order_by("district")
    )

    context = {
        "facilities": facilities,
        "districts": districts,
        "selected_district": district,
        "selected_ownership": ownership,
        "selected_type": facility_type,
        "search": search,
    }

    return render(request, "facilities/facility_list.html", context)
