function getCookie(c_name) {
    var i, x, y, ARRcookies = document.cookie.split(";");
    for (i = 0; i < ARRcookies.length; i++) {
        x = ARRcookies[i].substr(0, ARRcookies[i].indexOf("="));
        y = ARRcookies[i].substr(ARRcookies[i].indexOf("=") + 1);
        x = x.replace(/^\s+|\s+$/g, "");
        if (x == c_name) {
            return unescape(y);
        }
    }
}

function setCookie(c_name, value, exdays) {
    var exdate = new Date();
    exdate.setDate(exdate.getDate() + exdays);
    var c_value = escape(value) + ((exdays == null) ? "" : "; expires=" + exdate.toUTCString());
    document.cookie = c_name + "=" + c_value;
}

/* =========================================================
   checkForm — validates the search form before submission
   - Blocks submission if both fields are blank
   - Shows a popup if the user searches for "Elon Musk"
   ========================================================= */
function checkForm() {
    var originCity = document.getElementById('id_origin_city').value.trim();
    var destCity = document.getElementById('id_destination_city').value.trim();
    var destState = document.getElementById('id_destination_state').value.trim();

    // Block submission if all fields are empty
    if (originCity === '' && destCity === '' && destState === '') {
        alert('Please enter at least one search parameter.');
        return false;
    }

    return true;
}

/* =========================================================
   First-visit cookie redirect
   - First visit to the site: set cookie, go to splash page (/)
     unless already on the splash page (bonus: no redirect then)
   - Return visits: no redirect
   ========================================================= */
(function () {
    var COOKIE_NAME = 'visited';
    var COOKIE_DAYS = 365;

    function onDOMReady() {
        var alreadyVisited = getCookie(COOKIE_NAME);

        if (!alreadyVisited) {
            // First visit — set the cookie to mark the user as seen
            setCookie(COOKIE_NAME, 'true', COOKIE_DAYS);

            // Bonus: only redirect if NOT already on the splash page
            var onSplash = (window.location.pathname === '/' || window.location.pathname === '');
            if (!onSplash) {
                window.location.href = '/';
            }
        }
        // Return visitors: do nothing, let them stay on the current page
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', onDOMReady);
    } else {
        onDOMReady();
    }
}());

/* =========================================================
   Particle system — floating circles on a fixed canvas
   ========================================================= */
(function () {
    var PARTICLE_COUNT = 60;

    var canvas, ctx, particles;

    function initCanvas() {
        canvas = document.getElementById('particles-canvas');
        if (!canvas) return;
        ctx = canvas.getContext('2d');
        resizeCanvas();
        particles = [];
        for (var i = 0; i < PARTICLE_COUNT; i++) {
            particles.push(createParticle());
        }
        animate();
        window.addEventListener('resize', resizeCanvas);
    }

    function resizeCanvas() {
        if (!canvas) return;
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }

    function createParticle() {
        var size = Math.random() * 5 + 2;
        return {
            x: Math.random() * window.innerWidth,
            y: Math.random() * window.innerHeight,
            vx: (Math.random() - 0.5) * 0.6,
            vy: (Math.random() - 0.5) * 0.6,
            r: size,
            alpha: Math.random() * 0.4 + 0.1
        };
    }

    function animate() {
        if (!ctx) return;
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        for (var i = 0; i < particles.length; i++) {
            var p = particles[i];

            p.x += p.vx;
            p.y += p.vy;

            // Wrap around edges
            if (p.x < -p.r) p.x = canvas.width + p.r;
            if (p.x > canvas.width + p.r) p.x = -p.r;
            if (p.y < -p.r) p.y = canvas.height + p.r;
            if (p.y > canvas.height + p.r) p.y = -p.r;

            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(255, 255, 255, ' + p.alpha + ')';
            ctx.fill();
        }

        requestAnimationFrame(animate);
    }

    // Start once the DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCanvas);
    } else {
        initCanvas();
    }
}());