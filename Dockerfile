FROM pytorch/pytorch:2.4.1-cuda12.1-cudnn9-runtime

RUN conda install -y -c conda-forge \
       r-base=4.4 \
       r-causalimpact=1.4.1 \
       r-zoo \
   && conda clean -afy

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && python -m spacy download en_core_web_sm

WORKDIR /artifact
