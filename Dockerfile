FROM ubuntu:24.04

ARG FREECAD_REF=1.0.0

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        blender \
        build-essential \
        ca-certificates \
        cmake \
        git \
        libboost-date-time-dev \
        libboost-filesystem-dev \
        libboost-graph-dev \
        libboost-iostreams-dev \
        libboost-program-options-dev \
        libboost-python-dev \
        libboost-regex-dev \
        libboost-serialization-dev \
        libboost-thread-dev \
        libcoin-dev \
        libeigen3-dev \
        libgts-dev \
        libmedc-dev \
        libocct-data-exchange-dev \
        libocct-ocaf-dev \
        libocct-visualization-dev \
        libopencv-dev \
        libproj-dev \
        libpyside2-dev \
        libqt5opengl5-dev \
        libqt5svg5-dev \
        libqt5x11extras5-dev \
        libqt5xmlpatterns5-dev \
        libshiboken2-dev \
        libspnav-dev \
        libvtk9-dev \
        libx11-dev \
        libxerces-c-dev \
        libyaml-cpp-dev \
        libzipios++-dev \
        pyside2-tools \
        python3-dev \
        python3-matplotlib \
        python3-packaging \
        python3-pip \
        python3-pivy \
        python3-ply \
        python3-pyside2.qtcore \
        python3-pyside2.qtgui \
        python3-pyside2.qtnetwork \
        python3-pyside2.qtsvg \
        python3-pyside2.qtwidgets \
        qtbase5-dev \
        qttools5-dev \
        qtwebengine5-dev \
        swig \
        xauth \
        xvfb \
    && git clone --branch "${FREECAD_REF}" --depth 1 --recurse-submodules \
        https://github.com/FreeCAD/FreeCAD.git /tmp/freecad \
    && cmake -S /tmp/freecad -B /tmp/freecad/build \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/usr/local \
    && cmake --build /tmp/freecad/build --parallel "$(nproc)" \
    && cmake --install /tmp/freecad/build \
    && rm -rf /tmp/freecad /var/lib/apt/lists/*

WORKDIR /opt/patentar-converter
COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN python3 -m pip install --break-system-packages --no-cache-dir . \
    && useradd --create-home --uid 10001 converter

USER converter
WORKDIR /work

ENTRYPOINT ["xvfb-run", "-a", "python3", "-m", "patentar_converter"]
