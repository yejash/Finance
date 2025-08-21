from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from decimal import Decimal
from .models import Profile
from django.db.models import Sum
from expenses.models import Expense
from income.models import Income   # adjust import if Income is elsewhere
from datetime import date
from django.utils import timezone
from django.db.models.functions import TruncMonth
import datetime as dt


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            request.session['greeting_shown'] = False  # reset for each login
            return redirect('greeting')  # instead of dashboard
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match!')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken!')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered!')
        else:
            User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, 'Account created successfully! You can log in now.')
            return redirect('login')
    return render(request, 'register.html')

def upload_avatar(request):
    if request.method == "POST":
        avatar = request.FILES.get('avatar')
        if avatar:
            profile = Profile.objects.get(user=request.user)
            profile.avatar = avatar
            profile.save()
            return redirect('profile')  # change 'profile' to your URL name
    return render(request, 'upload_avatar.html')


def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if User.objects.filter(email=email).exists():
            # send reset email (dummy example)
            send_mail(
                'Password Reset Request',
                'Click the link below to reset your password.',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False
            )
            messages.success(request, 'Password reset email sent!')
        else:
            messages.error(request, 'Email not found!')
    return render(request, 'forgot_password.html')



# Try import Income model if you have one; otherwise ignore
try:
    from income.models import Income
    HAVE_INCOME = True
except Exception:
    HAVE_INCOME = False

# @login_required
# def dashboard(request):
#     user = request.user

#     # ---------- totals ----------
#     if HAVE_INCOME:
#         income_agg = Income.objects.filter(user=user).aggregate(total=Sum('amount'))['total']
#     else:
#         income_agg = None
#     expense_agg = Expense.objects.filter(user=user).aggregate(total=Sum('amount'))['total']

#     total_income = Decimal(income_agg) if income_agg is not None else Decimal('0.00')
#     total_expense = Decimal(expense_agg) if expense_agg is not None else Decimal('0.00')
#     balance = total_income - total_expense

#     # transactions count
#     tx_count = Expense.objects.filter(user=user).count()
#     if HAVE_INCOME:
#         tx_count += Income.objects.filter(user=user).count()

#     # ---------- recent transactions (combine, sort, limit to 5) ----------
#     # We'll fetch up to 10 from each side (to have enough to merge) and then pick the 5 newest
#     recent_items = []

#     # helper to produce sortable ISO timestamp string (always a string)
#     def _iso_ts(obj):
#         created = getattr(obj, "created_at", None)
#         if created:
#             return created.isoformat()
#         # if only a date field is present, make iso datetime at midnight
#         d = getattr(obj, "date", None)
#         if isinstance(d, dt.date) and not isinstance(d, dt.datetime):
#             return dt.datetime.combine(d, dt.time.min).isoformat()
#         return str(d)

#     # expenses
#     for e in Expense.objects.filter(user=user).order_by('-date')[:10]:
#         recent_items.append({
#             "id": e.id,
#             "date": getattr(e, "date", None),
#             "description": getattr(e, "description", ""),
#             "amount": float(getattr(e, "amount", 0)),
#             "type": "expense",
#             "timestamp": _iso_ts(e),
#         })

#     # incomes (if available)
#     if HAVE_INCOME:
#         for i in Income.objects.filter(user=user).order_by('-date')[:10]:
#             recent_items.append({
#                 "id": i.id,
#                 "date": getattr(i, "date", None),
#                 "description": getattr(i, "description", ""),
#                 "amount": float(getattr(i, "amount", 0)),
#                 "type": "income",
#                 "timestamp": _iso_ts(i),
#             })

#     # sort by timestamp (ISO strings sort lexicographically in chronological order) and take top 5
#     recent_sorted = sorted(recent_items, key=lambda x: x["timestamp"], reverse=True)[:5]

#     # ---------- monthly chart data (last 6 months) ----------
#     months_count = 6
#     today = timezone.localdate()
#     start_idx = today.year * 12 + today.month - 1 - (months_count - 1)
#     months = []
#     for j in range(months_count):
#         idx = start_idx + j
#         y = idx // 12
#         m = idx % 12 + 1
#         months.append(date(y, m, 1))
#     start_date = months[0]

#     # incomes aggregation (guarded)
#     inc_map = {}
#     if HAVE_INCOME:
#         incomes_qs = (
#             Income.objects.filter(user=user, date__gte=start_date)
#             .annotate(month=TruncMonth("date"))
#             .values("month")
#             .annotate(total=Sum("amount"))
#             .order_by("month")
#         )
#         for r in incomes_qs:
#             mon = r["month"]
#             if hasattr(mon, "date"):
#                 mon = mon.date()
#             inc_map[(mon.year, mon.month)] = float(r["total"] or 0)

#     # expenses aggregation
#     exp_map = {}
#     expenses_qs = (
#         Expense.objects.filter(user=user, date__gte=start_date)
#         .annotate(month=TruncMonth("date"))
#         .values("month")
#         .annotate(total=Sum("amount"))
#         .order_by("month")
#     )
#     for r in expenses_qs:
#         mon = r["month"]
#         if hasattr(mon, "date"):
#             mon = mon.date()
#         exp_map[(mon.year, mon.month)] = float(r["total"] or 0)

#     labels = [m.strftime("%b %Y") for m in months]
#     income_values = [inc_map.get((m.year, m.month), 0) for m in months]
#     expense_values = [exp_map.get((m.year, m.month), 0) for m in months]

#     # ---------- final context (IMPORTANT: pass recent_sorted, not recent_items) ----------
#     context = {
#         "total_income": float(total_income),
#         "total_expense": float(total_expense),
#         "transactions_count": tx_count,
#         "balance": float(balance),
#         "recent_transactions": recent_sorted,   # <-- only 5 items here
#         "month_labels": labels,
#         "income_values": income_values,
#         "expense_values": expense_values,
#     }

    
#     return render(request, "dashboard.html", context)


@login_required
def dashboard(request):
    user = request.user

    # ---------- totals ----------
    if HAVE_INCOME:
        income_agg = Income.objects.filter(user=user).aggregate(total=Sum('amount'))['total']
    else:
        income_agg = None
    expense_agg = Expense.objects.filter(user=user).aggregate(total=Sum('amount'))['total']

    total_income = Decimal(income_agg) if income_agg is not None else Decimal('0.00')
    total_expense = Decimal(expense_agg) if expense_agg is not None else Decimal('0.00')
    balance = total_income - total_expense

    # transactions count
    tx_count = Expense.objects.filter(user=user).count()
    if HAVE_INCOME:
        tx_count += Income.objects.filter(user=user).count()

    # ---------- recent transactions (combine, sort, limit to 5) ----------
    recent_items = []

    def _iso_ts(obj):
        created = getattr(obj, "created_at", None)
        if created:
            return created.isoformat()
        d = getattr(obj, "date", None)
        if isinstance(d, dt.date) and not isinstance(d, dt.datetime):
            return dt.datetime.combine(d, dt.time.min).isoformat()
        return str(d)

    for e in Expense.objects.filter(user=user).order_by('-date')[:10]:
        recent_items.append({
            "id": e.id,
            "date": getattr(e, "date", None),
            "description": getattr(e, "description", ""),
            "amount": float(getattr(e, "amount", 0)),
            "type": "expense",
            "timestamp": _iso_ts(e),
        })

    if HAVE_INCOME:
        for i in Income.objects.filter(user=user).order_by('-date')[:10]:
            recent_items.append({
                "id": i.id,
                "date": getattr(i, "date", None),
                "description": getattr(i, "description", ""),
                "amount": float(getattr(i, "amount", 0)),
                "type": "income",
                "timestamp": _iso_ts(i),
            })

    recent_sorted = sorted(recent_items, key=lambda x: x["timestamp"], reverse=True)[:5]

    # ---------- monthly chart data (last 6 months) ----------
    months_count = 6
    today = timezone.localdate()
    start_idx = today.year * 12 + today.month - 1 - (months_count - 1)
    months = []
    for j in range(months_count):
        idx = start_idx + j
        y = idx // 12
        m = idx % 12 + 1
        months.append(date(y, m, 1))
    start_date = months[0]

    inc_map = {}
    if HAVE_INCOME:
        incomes_qs = (
            Income.objects.filter(user=user, date__gte=start_date)
            .annotate(month=TruncMonth("date"))
            .values("month")
            .annotate(total=Sum("amount"))
            .order_by("month")
        )
        for r in incomes_qs:
            mon = r["month"]
            if hasattr(mon, "date"):
                mon = mon.date()
            inc_map[(mon.year, mon.month)] = float(r["total"] or 0)

    exp_map = {}
    expenses_qs = (
        Expense.objects.filter(user=user, date__gte=start_date)
        .annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )
    for r in expenses_qs:
        mon = r["month"]
        if hasattr(mon, "date"):
            mon = mon.date()
        exp_map[(mon.year, mon.month)] = float(r["total"] or 0)

    labels = [m.strftime("%b %Y") for m in months]
    income_values = [inc_map.get((m.year, m.month), 0) for m in months]
    expense_values = [exp_map.get((m.year, m.month), 0) for m in months]

    # ---------- MODE aggregates for doughnut charts ----------
    # Income by mode (if Income model exists)
    income_mode_labels = []
    income_mode_values = []
    if HAVE_INCOME:
        income_modes_qs = (
            Income.objects.filter(user=user)
            .values('mode')
            .annotate(total=Sum('amount'))
            .order_by('-total')
        )
        for r in income_modes_qs:
            income_mode_labels.append(r['mode'] or 'Unknown')
            income_mode_values.append(float(r['total'] or 0))

    # Expense by mode
    expense_mode_labels = []
    expense_mode_values = []
    expense_modes_qs = (
        Expense.objects.filter(user=user)
        .values('mode')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )
    for r in expense_modes_qs:
        expense_mode_labels.append(r['mode'] or 'Unknown')
        expense_mode_values.append(float(r['total'] or 0))

    # ---------- final context ----------
    context = {
        "total_income": float(total_income),
        "total_expense": float(total_expense),
        "transactions_count": tx_count,
        "balance": float(balance),
        "recent_transactions": recent_sorted,
        "month_labels": labels,
        "income_values": income_values,
        "expense_values": expense_values,
        # mode chart data:
        "income_mode_labels": income_mode_labels,
        "income_mode_values": income_mode_values,
        "expense_mode_labels": expense_mode_labels,
        "expense_mode_values": expense_mode_values,
    }

    return render(request, "dashboard.html", context)



@login_required
def greeting_view(request):
    # If greeting is already shown, skip directly to dashboard
    if request.session.get('greeting_shown'):
        return redirect('dashboard')

    request.session['greeting_shown'] = True  # mark as shown
    return render(request, 'greeting.html')

    context = {
        'profile': profile,
        # 'total_income': total_income,
        # 'total_expense': total_expense,
        # 'balance': balance,
    }
    return render(request, 'dashboard.html', context)

def about_view(request):
    return render(request,'about.html')

def expenses_view(request):
    return render(request,'expenses.html')

