from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect,HttpResponseBadRequest,FileResponse, Http404, JsonResponse
from django.urls import reverse
from django.db import IntegrityError
from .models import User
from django.contrib.auth.decorators import login_required
# Create your views here.
def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = "noemail@email.com"
        if len(username) > 30:
          return render(request, "register.html", {
                "message": "Username too long"
            })
        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "register.html")

#RESTART BUTTON
def restart(request):
    if request.method=="POST":
        request.user.point = 0 
        request.session["atom_gain"] = 1
        request.session["plus_one_cost"] = 10
        request.session["times_two_cost"] = 1000
        request.session["auto_clicker_active"] = False
        request.session["auto_clicker_gain"] = 1
        request.session["model_right_now"] = "dalton"
        #RESETS MODELS
        request.session["model_thomson_purchased"] = False
        request.session["model_rutherford_purchased"] = False
        request.session["model_bohr_purchased"] = False
        request.session["model_current_purchased"] = False
        request.session["model_multiplier"] = 1
        request.user.save()
        
    return redirect('index')

def apply_model_prestige(request, model_name, cost, flag_name):
    if request.user.point >= cost and not request.session.get(flag_name, False):
        # Reset upgrades
        request.session["atom_gain"] = 1
        request.session["plus_one_cost"] = 10
        request.session["times_two_cost"] = 1000
        request.session["times_two_level"] = 0
        request.session["auto_clicker_active"] = False
        request.session["auto_clicker_gain"] = 1
        request.user.point = 0

        # Apply multiplier
        request.session["model_multiplier"] = request.session.get("model_multiplier", 1) * 2

        # Update model state
        request.session["model_right_now"] = model_name
        request.session[flag_name] = True
        request.user.save()
        return True
    return False

def auto_clicker_tick(request):

    if request.method == "POST" and request.session.get("auto_clicker_active"):
        atom_gain = request.session.get("atom_gain", 1)
        multiplier = request.session.get("model_multiplier", 1)

        gain = atom_gain * multiplier
        request.user.point += gain
        request.user.save()

        return JsonResponse({"point": request.user.point})

    return JsonResponse({"point": request.user.point})

def click_atom(request):
    if request.method == "POST":
        atom_gain = request.session.get("atom_gain", 1)
        multiplier = request.session.get("model_multiplier", 1)
        gain = atom_gain * multiplier

        request.user.point += gain
        request.user.save()

        return JsonResponse({"point": request.user.point})
    return JsonResponse({"error": "Invalid request"})

@login_required(login_url='login')

def index(request):
    #FOR ATOM PLUS ONE
    if "atom_gain" not in request.session:
        request.session["atom_gain"] = 1
    if "plus_one_cost" not in request.session:
        request.session["plus_one_cost"] = 10  # Starting cost
    
    #FOR ATOM TIMES TWO
    if "times_two_cost" not in request.session:
        request.session["times_two_cost"] = 1000
    if "times_two_level" not in request.session:
        request.session["times_two_level"] = 0
    #FOR AUTOCLICKER
    if "auto_clicker_active" not in request.session:
        request.session["auto_clicker_active"] = False

    if "auto_clicker_gain" not in request.session:
        request.session["auto_clicker_gain"] = 1  # atoms per tick

    #FOR MODEL UPGRADES
    if "model_multiplier" not in request.session:
        request.session["model_multiplier"] = 1

    if "model_right_now" not in request.session:
        request.session["model_right_now"] = "dalton"

    if "model_thomson_purchased" not in request.session:
        request.session["model_thomson_purchased"] = False

    if "model_rutherford_purchased" not in request.session:
        request.session["model_rutherford_purchased"] = False

    if "model_bohr_purchased" not in request.session:
        request.session["model_bohr_purchased"] = False

    if "model_current_purchased" not in request.session:
        request.session["model_current_purchased"] = False

    if request.method=="POST":
        user_action = request.POST.get("action")
        if user_action == "click":
            base_gain = request.session["atom_gain"]
            model = request.session["model_right_now"]
            multiplier = request.session.get("model_multiplier", 1)

            # Only apply multiplier if model is beyond Dalton
            if model != "dalton":
                gain = base_gain * multiplier
            else:
                gain = base_gain

            request.user.point += gain
            request.user.save()
            point = request.user.point
                
        elif user_action == "upgrade_gain":
            upgrade_name = request.POST.get("upgrade_name")
            if upgrade_name == "plus_one":
                #Increase atom gain per click
                cost = request.session["plus_one_cost"]
                if request.user.point >= cost: 
                    request.user.point -= cost
                    request.session["atom_gain"] += 1
                    request.session["plus_one_cost"] = int(cost**1.05) #Increase cost
                    request.user.save()
                else:
                    pass
            elif upgrade_name == "times_two":
                #Increase atmo gain by a factor of 2
                mult_cost = request.session["times_two_cost"]
                level = request.session.get("times_two_level", 0)

                if request.user.point >= mult_cost:
                    request.user.point -= mult_cost
                    request.session["atom_gain"] *= 2
                    request.session["times_two_level"] = level + 1
                    
                    #recalculate cost using exponential scales!!!!
                    new_level = level + 1
                    request.session["times_two_cost"] = int(1000 * (1.5 ** new_level)) #Increase cost
                    request.user.save()
                else:
                    pass
            elif upgrade_name == "auto_clicker":
                # Start auto-clicker
                clicker_cost = 100
                if request.user.point >= clicker_cost and not request.session.get("auto_clicker_active", False):
                    request.user.point -= clicker_cost
                    request.session["auto_clicker_active"] = True
                    request.session["auto_clicker_gain"] = request.session["atom_gain"] #number of atoms per tick
                    request.user.save()
                else:
                    pass
                
        elif user_action == "upgrade_model":

            upgrade_name = request.POST.get("upgrade_name")

            if upgrade_name == "thomson" and request.session["model_right_now"] == "dalton":
                if apply_model_prestige(request, "thomson", 5000, "model_thomson_purchased"):
                    return redirect('index')

            elif upgrade_name == "rutherford" and request.session["model_right_now"] == "thomson":
                if apply_model_prestige(request, "rutherford", 50000, "model_rutherford_purchased"):
                    return redirect('index')

            elif upgrade_name == "bohr" and request.session["model_right_now"] == "rutherford":
                if apply_model_prestige(request, "bohr", 500000, "model_bohr_purchased"):
                    return redirect('index')

            elif upgrade_name == "current" and request.session["model_right_now"] == "bohr":
                if apply_model_prestige(request, "current", 10000000, "model_current_purchased"):
                    return redirect('index')

     # Choose image based on point count
    model = request.session["model_right_now"]
    point = request.user.point
    if model == "dalton":
        image_path = "images/black_sphere.png"
        button_text = "Dalton model"
        fun_fact = "FUN FACT ABOUT DALTON: Dalton helped further research on color blindness by donating his eyes after his death. Dalton believed that the liquid behind your eye was a filter for colors and that he was missing something since he couldn’t see all colors. After the autopsy it was discovered that the liquid was colorless meaning his theory was wrong. However DNA analysis shows that Dalton was missing a receptor for green."
        info_on_model = "THE DALTON MODEL: John Dalton was the first scientist to create a modern atomic theory, which stated that atoms are the smallest forms of elements, atoms of the same element have the same atomic mass, and thus atoms of different elements have different masses. The Dalton model only has a nucleus."
    elif model == "thomson":
        image_path = "images/thomson.png"
        button_text = "Thomson model"
        fun_fact = "FUN FACT ABOUT THOMSON: J. J. Thomson received the Nobel Prize in Physics in 1906, and so did his son, George Paget Thomson, in 1937.  He worked as a master for Trinity College, and a total of seven Nobel Prizes were awarded those who worked under him."
        info_on_model = "THE THOMSON MODEL: J. J. Thomson’s atomic theory is known as the Plum Pudding model, proposing that atoms are spheres of positive charge with electrons contained inside.  He came up with this model because he observed that cathode rays (electrons) were negatively charged, so the rest of the atom must be positive to make the atom neutral."

    elif model == "rutherford":
        image_path = "images/rutherford.png" 
        button_text = "Rutherford model"
        fun_fact = "FUN FACT ABOUT RUTHERFORD: Rutherford is known as the father of nuclear physics, discovering concepts such as radioactive half-life, alpha and beta radiation, and radon.  Rutherford’s face is featured on the front of the New Zealand $100 bill, and element 104, rutherfordium, is named after him."
        info_on_model = "THE RUTHERFORD MODEL: Ernest Rutherford was the creator of the nuclear model, showing that an atom consists of a small, dense, positively charged nucleus that is surrounded by orbiting electrons and mostly empty space.  Rutherford came to this conclusion after observing how positively charged alpha particles passed through gold foil, but a few were deflected by presumably small particles with a positive charge."

    elif model == "bohr":
        image_path = "images/bohr.png"
        button_text = "Bohr model"
        fun_fact = "FUN FACT ABOUT BOHR: Bohr played goalkeeper on a competitive soccer team with his brother, who won an Olympic silver medal.  Just like Thomson, Bohr’s son, Aage N. Bohr won a Nobel Prize in Physics in 1975, and the element bohrium was named in his honor."
        info_on_model = "THE BOHR MODEL: Neils Bohr improved off of Rutherford’s model by addressing how electrons fit in the atomic model.  Bohr’s model says that electrons travel in specific orbits around the nucleus, and electrons can absorb or emit energy in order to jump to a different energy level or shell.  Bohr observed this emission of energy in the form of light, and the fact that different elements when heated emitted different wavelengths suggested that different elements had different energy amounts per level and interval/jump."

    elif model == "current":
        image_path = "images/modern.png"
        button_text = "Modern model"
        fun_fact = "FUN FACT ABOUT SCHRODINGER, EINSTEN, AND HEISENBERG: Schrodinger would tell people that asked him if the cat was alive or dead that they should ask the cat. Einsten really enjoyed sailing however he was not too skilled and capsized multiple times. Schrodinger also made a book What is Life? that inspired the discovery of DNA, Watson and Crick credited him with his ideas. Heseinberg has a crater on the moon named after him because he had great contributions toward quantum mechanics that they gave him the honor of naming the crater after him."
        info_on_model = "THE CURRENT MODEL: When Erwin Schrödinger began his work (around 1925–1926), Niels Bohr’s atomic model (1913) was still the best available theory to describe the structure of the atom. Bohr’s model explained the hydrogen atom’s spectral lines using quantized orbits — electrons moving in fixed circular paths around the nucleus. He was able to verify the energy levels using the new method and found that they catch up with Bohr. Schrödinger transformed Bohr’s discrete orbits into wave-like probability clouds."
    return render(request, 'index.html', {
        'point': point,
        'image_path': image_path,
        'button_text' : button_text,
        'fun_fact' : fun_fact,
        'info_on_model' : info_on_model,
        'atom_gain': request.session.get("atom_gain", 1),
        'plus_one_cost': request.session["plus_one_cost"],
        'times_two_cost': request.session["times_two_cost"],
        'auto_clicker_active': request.session.get("auto_clicker_active", False),
        'model_right_now': request.session.get("model_right_now"),
        'model_thomson_purchased': request.session.get("model_thomson_purchased", False),
        'model_rutherford_purchased': request.session.get("model_rutherford_purchased", False),
        'model_bohr_purchased': request.session.get("model_bohr_purchased", False),
        'model_current_purchased': request.session.get("model_current_purchased", False),
        'model_multiplier': request.session.get("model_multiplier", 1)
        })

