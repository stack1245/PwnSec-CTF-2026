(function () {
  "use strict";

  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)");

  function decorate() {
    var towers = document.querySelectorAll(".bld");
    var signCount = 0;

    for (var i = 0; i < towers.length; i++) {
      var el = towers[i];
      var spire = parseInt(el.style.getPropertyValue("--spire") || "0", 10);
      var sign = parseInt(el.style.getPropertyValue("--sign") || "0", 10);

      if (spire > 0) {
        var dot = document.createElement("span");
        dot.className = "beacon";
        dot.style.bottom = "calc(100% + " + spire * 9 + "px)";
        dot.style.animationDelay = (i % 7) * 0.8 + "s";
        el.appendChild(dot);
      }

      if (sign > 0 && signCount < 4 && i % 5 === 0) {
        el.classList.add("flicker");
        el.style.animationDelay = (i % 3) * 3.1 + "s";
        signCount++;
      }
    }
  }

  var MAX_SCROLL = 900;
  var layers = [];
  var target = 0;
  var current = 0;
  var frame = null;

  function collect() {
    var nodes = document.querySelectorAll(".sky [data-depth]");
    layers = [];
    for (var i = 0; i < nodes.length; i++) {
      layers.push({ el: nodes[i], depth: parseFloat(nodes[i].dataset.depth) || 0 });
    }
  }

  function paint() {
    frame = null;
    for (var i = 0; i < layers.length; i++) {
      var offset = -(current * layers[i].depth);
      layers[i].el.style.transform =
        "translate3d(0," + offset.toFixed(2) + "px,0)";
    }
  }

  function schedule() {
    if (frame === null) {
      frame = window.requestAnimationFrame(paint);
    }
  }

  function onScroll() {
    var y = window.scrollY || window.pageYOffset || 0;
    target = y > MAX_SCROLL ? MAX_SCROLL : y;
    /* eased, not 1:1 with the scrollbar */
    var next = current + (target - current) * 0.18;
    if (Math.abs(next - target) < 0.15) next = target;
    current = next;
    schedule();
    if (current !== target) window.requestAnimationFrame(onScroll);
  }

  function start() {
    if (reduce.matches) return;
    collect();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", collect, { passive: true });
    onScroll();
  }

  function toast(msg) {
    var el = document.querySelector(".toast");
    if (!el) {
      el = document.createElement("div");
      el.className = "toast";
      document.body.appendChild(el);
    }
    el.textContent = msg;
    el.classList.add("is-on");
    window.setTimeout(function () {
      el.classList.remove("is-on");
    }, 1600);
  }

  function wireCopy() {
    var buttons = document.querySelectorAll("[data-copy]");
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].addEventListener("click", function () {
        var node = document.querySelector(this.getAttribute("data-copy"));
        if (!node) return;
        var text = node.textContent.trim();
        var done = function () { toast("designation copied"); };
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).then(done, function () {
            toast("copy blocked by browser");
          });
        } else {
          toast(text);
        }
      });
    }
  }

  function boot() {
    decorate();
    wireCopy();
    start();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
