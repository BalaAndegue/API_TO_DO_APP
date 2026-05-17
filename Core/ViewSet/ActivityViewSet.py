from django.utils.decorators import method_decorator
from rest_framework import viewsets, permissions, mixins
from django.db.models import Q
from Core.models import Activity
from Core.serializers import ActivitySerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

_ACTIVITY_FILTERS = [
    openapi.Parameter('board', openapi.IN_QUERY, type=openapi.TYPE_INTEGER,
                      description='Filtrer par tableau (board_id).'),
    openapi.Parameter('card', openapi.IN_QUERY, type=openapi.TYPE_INTEGER,
                      description='Filtrer par carte (card_id).'),
]


@method_decorator(name='list', decorator=swagger_auto_schema(
    operation_summary='Fil d\'activité',
    operation_description=(
        'Retourne le journal des actions sur les tableaux accessibles, trié du plus récent au plus ancien. '
        'Les activités sont créées **automatiquement** par les signaux Django — cet endpoint est en **lecture seule**.\n\n'
        '**Types d\'action :** `create_board`, `join_board`, `leave_board`, '
        '`add_comment`, `delete_comment`, `check_item`, `uncheck_item`.\n\n'
        'Filtres : **?board=<id>** ou **?card=<id>**.'
    ),
    manual_parameters=_ACTIVITY_FILTERS,
    tags=['Activity'],
))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(
    operation_summary='Détail d\'une entrée d\'activité',
    tags=['Activity'],
))
class ActivityViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ActivitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Activity.objects.none()
        user = self.request.user
        qs = Activity.objects.filter(
            Q(board__visibility='public') |
            Q(board__board_members__user=user) |
            Q(board__creator=user)
        ).distinct()
        board_id = self.request.query_params.get('board')
        card_id = self.request.query_params.get('card')
        if board_id:
            qs = qs.filter(board_id=board_id)
        if card_id:
            qs = qs.filter(card_id=card_id)
        return qs.select_related('board', 'card', 'list', 'user')
