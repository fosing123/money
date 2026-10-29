from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from finance.models import Transaction


@login_required
def ai_chat_view(request):
    context = {'configured': bool(settings.AI_API_KEY), 'message': 'AI is not configured yet. Add AI_API_KEY in your environment to enable live guidance.'}
    if request.method == 'POST':
        prompt = request.POST.get('prompt', '').strip()
        if not prompt:
            context['error'] = 'Please ask a question.'
            return render(request, 'ai_assistant/chat.html', context)
        if not settings.AI_API_KEY:
            context['response'] = 'The AI assistant is disabled because no provider key has been configured. You can still use the dashboard and budget tools.'
            context['history'] = [{'prompt': prompt, 'response': context['response']}]
            return render(request, 'ai_assistant/chat.html', context)
        transactions = Transaction.objects.filter(owner=request.user)[:10]
        context['response'] = f'AI guidance is ready. Based on {len(transactions)} recent transactions, I can help review spending patterns and goals once the provider is configured.'
        context['history'] = [{'prompt': prompt, 'response': context['response']}]
    return render(request, 'ai_assistant/chat.html', context)
