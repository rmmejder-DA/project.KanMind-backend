# Anleitung: urlpatterns, Views und Serializer in Django REST Framework

Diese Anleitung ist als Vorlage gedacht und kann in jedem Django-/DRF-Projekt verwendet werden.
Die Beispiele stammen aus diesem Projekt (`user_auth_app`).

---

## 1. Überblick: Wie hängt alles zusammen?

```
Request  ->  project/urls.py  ->  app/api/urls.py  ->  app/api/views.py  ->  app/api/serializers.py  ->  app/models.py
                (include)           (urlpatterns)         (View-Klassen)        (Daten prüfen/umwandeln)     (Datenbank)
```

| Datei | Aufgabe |
|---|---|
| `models.py` | Datenbankmodelle (Tabellen) |
| `api/serializers.py` | Wandelt Modelle in JSON um und prüft eingehende Daten |
| `api/views.py` | Verarbeitet Requests (GET, POST, ...) und gibt Responses zurück |
| `api/urls.py` | Ordnet URLs den Views zu (`urlpatterns`) |
| Projekt-`urls.py` | Bindet die `api/urls.py` der Apps mit `include()` ein |

---

## 2. Models (`models.py`)

```python
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.user.username
```

Nach Änderungen an Models immer:

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 3. Serializer (`api/serializers.py`)

Ein `ModelSerializer` erzeugt die Felder automatisch aus dem Model.

```python
from rest_framework import serializers
from user_auth_app.models import UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['user', 'bio', 'location']
```

Eigene Validierung und Logik:

```python
class RegistrationSerializer(serializers.ModelSerializer):
    repeated_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'repeated_password']
        extra_kwargs = {'password': {'write_only': True}}

    # Feldvalidierung: validate_<feldname>
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists')
        return value
```

---

## 4. Views (`api/views.py`)

### 4.1 Generische Views (Standardfall)

| Klasse | Methoden | Typischer Einsatz |
|---|---|---|
| `ListAPIView` | GET (Liste) | nur lesen, Liste |
| `CreateAPIView` | POST | nur anlegen |
| `ListCreateAPIView` | GET, POST | Liste + anlegen |
| `RetrieveAPIView` | GET (ein Objekt) | nur lesen, Detail |
| `RetrieveUpdateDestroyAPIView` | GET, PUT, PATCH, DELETE | Detail, bearbeiten, löschen |

```python
from rest_framework import generics
from user_auth_app.models import UserProfile
from .serializers import UserProfileSerializer

class UserProfileList(generics.ListCreateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer

class UserProfileDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
```

### 4.2 APIView (eigene Logik)

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

class RegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            account = serializer.save()
            return Response({'username': account.username, 'email': account.email})
        return Response(serializer.errors, status=400)
```

> Tipp: Mit `status=400` (bzw. `201` bei Erstellung) liefert die API korrekte HTTP-Statuscodes.
> Das Beispiel in diesem Projekt gibt bei Fehlern ohne Statuscode `200` zurück.

### 4.3 Login mit Token (Vererbung von `ObtainAuthToken`)

```python
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

class CustomLogin(ObtainAuthToken):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key, 'username': user.username, 'email': user.email})
        return Response(serializer.errors, status=400)
```

### 4.4 Funktionsbasierte Views (Alternative)

```python
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def health(request):
    return Response({'status': 'ok'})
```

---

## 5. URLs (`api/urls.py`)

```python
from django.urls import path
from .views import UserProfileList, UserProfileDetail, RegistrationView, CustomLogin

urlpatterns = [
    path('profiles/', UserProfileList.as_view(), name='userprofile-list'),
    path('profiles/<int:pk>/', UserProfileDetail.as_view(), name='userprofile-detail'),
    path('registration/', RegistrationView.as_view(), name='registration'),
    path('login/', CustomLogin.as_view(), name='login'),
]
```

### Wichtige Regeln

- **Klassen-Views** immer mit `.as_view()` einbinden.
- **Funktions-Views** ohne `.as_view()`: `path('health/', health)`.
- **Pfad-Parameter:** `<int:pk>`, `<str:slug>`, `<uuid:id>`, `<slug:name>`.
- **`name=`** vergeben, damit man URLs mit `reverse()` erzeugen kann.
- **Trailing Slash** konsequent verwenden (`'profiles/'`). Ohne `/` am Ende gibt es bei Django-Redirects Probleme mit POST.

---

## 6. Projekt-URLs einbinden (`project/urls.py`)

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('user_auth_app.api.urls')),
    path('api/market/', include('market_app.api.urls')),
    path('api-auth/', include('rest_framework.urls')),  # Login/Logout im Browser-Interface
]
```

`include()` bindet die `urlpatterns` einer App unter einem Präfix ein.
Die Endpunkte lauten dann z. B. `/api/auth/profiles/` und `/api/auth/login/`.

---

## 7. Wiederverwendbare Vorlage für eine neue App

Ordnerstruktur:

```
meine_app/
├── models.py
└── api/
    ├── __init__.py
    ├── serializers.py
    ├── views.py
    └── urls.py
```

**`api/views.py`**
```python
from rest_framework import generics
from meine_app.models import Eintrag
from .serializers import EintragSerializer

class EintragList(generics.ListCreateAPIView):
    queryset = Eintrag.objects.all()
    serializer_class = EintragSerializer

class EintragDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Eintrag.objects.all()
    serializer_class = EintragSerializer
```

**`api/serializers.py`**
```python
from rest_framework import serializers
from meine_app.models import Eintrag

class EintragSerializer(serializers.ModelSerializer):
    class Meta:
        model = Eintrag
        fields = '__all__'
```

**`api/urls.py`**
```python
from django.urls import path
from .views import EintragList, EintragDetail

urlpatterns = [
    path('eintraege/', EintragList.as_view(), name='eintrag-list'),
    path('eintraege/<int:pk>/', EintragDetail.as_view(), name='eintrag-detail'),
]
```

**Projekt-`urls.py`**
```python
path('api/meine-app/', include('meine_app.api.urls')),
```

**`settings.py`** – App und DRF registrieren:
```python
INSTALLED_APPS = [
    # ...
    'rest_framework',
    'rest_framework.authtoken',  # nötig für Token-Login
    'meine_app',
]
```

---

## 8. Häufige Fehler

| Problem | Ursache / Lösung |
|---|---|
| `404 Not Found` | Pfad falsch, Trailing Slash fehlt oder `include()` fehlt in Projekt-`urls.py` |
| `TypeError: 'type' object is not callable` | View ohne `.as_view()` eingebunden |
| `ImportError` bei `from .views import ...` | Name in `views.py` stimmt nicht oder zirkulärer Import |
| `NoReverseMatch` | `name=` in `urlpatterns` fehlt oder falsch geschrieben |
| `401 Unauthorized` / `403 Forbidden` | Fehlende Berechtigung; `permission_classes` prüfen oder `Authorization: Token <key>` Header senden |
| Token-Login funktioniert nicht | `rest_framework.authtoken` nicht in `INSTALLED_APPS` oder keine Migration ausgeführt |

---

## 9. Testen

Beispiel mit `curl` (Windows PowerShell: `curl.exe` verwenden):

```bash
curl -X POST http://127.0.0.1:8000/api/auth/registration/ -H "Content-Type: application/json" -d "{\"username\":\"max\",\"email\":\"max@example.com\",\"password\":\"geheim123\",\"repeated_password\":\"geheim123\"}"

curl -X POST http://127.0.0.1:8000/api/auth/login/ -H "Content-Type: application/json" -d "{\"username\":\"max\",\"password\":\"geheim123\"}"

curl http://127.0.0.1:8000/api/auth/profiles/ -H "Authorization: Token <token>"
```
