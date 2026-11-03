from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .models import ChatMessage
from .services import AIConfigurationError, AIServiceError, generate_money_guidance


def _load_chat_history(user):
    history = list(ChatMessage.objects.filter(user=user)[:12])
    history.reverse()
    return history


@login_required
@require_http_methods(["GET", "POST"])
async def ai_chat_view(request):
    configured = bool(
        (getattr(settings, "GEMINI_API_KEY", "") or getattr(settings, "AI_API_KEY", ""))
        and getattr(settings, "AI_PROVIDER", "gemini").lower() == "gemini"
    )
    error = ""
    submitted_prompt = ""

    if request.method == "POST":
        submitted_prompt = request.POST.get("prompt", "").strip()
        if not submitted_prompt:
            error = "Tell me a little about what's on your mind first."
        elif len(submitted_prompt) > 1500:
            error = "Keep your message under 1,500 characters so we can work through it together."
        elif configured:
            try:
                response = await generate_money_guidance(request.user, submitted_prompt)
            except (AIConfigurationError, AIServiceError) as exc:
                error = str(exc)
                response = ""
            if response:
                await sync_to_async(ChatMessage.objects.create, thread_sensitive=True)(
                    user=request.user,
                    prompt=submitted_prompt,
                    response=response,
                )
                messages.success(request, "Your message is saved in your private TIANA chat history.")
                return redirect("ai_chat")
        else:
            response = (
                "I'm not connected to Gemini on the server yet, so I won't pretend this is a live AI answer. "
                "While that gets configured, try checking your Transactions and Budgets pages, then start with "
                "one small change that feels realistic for this week."
            )
            await sync_to_async(ChatMessage.objects.create, thread_sensitive=True)(
                user=request.user,
                prompt=submitted_prompt,
                response=response,
            )
            messages.success(request, "Your message is saved in your private TIANA chat history.")
            return redirect("ai_chat")

    history = await sync_to_async(_load_chat_history, thread_sensitive=True)(request.user)
    return await sync_to_async(render, thread_sensitive=True)(request, "ai_assistant/chat.html", {
        "configured": configured,
        "error": error,
        "history": history,
        "submitted_prompt": submitted_prompt,
    })
