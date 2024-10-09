# from django.shortcuts import redirect
# from django.urls import reverse
#
# class HandleErrorsMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response
#
#     def __call__(self, request):
#         response = self.get_response(request)
#         return response
#
#     def process_exception(self, request, exception):
#         # Redirect to the close function on exceptions
#         return redirect(reverse('close'))
