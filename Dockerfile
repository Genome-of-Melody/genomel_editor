FROM python:3.11-bullseye

RUN pip install --upgrade pip

# Download and install Anaconda3
RUN apt-get update && apt-get install -y wget bzip2 \
    && rm -rf /var/lib/apt/lists/* \
    && wget https://repo.anaconda.com/archive/Anaconda3-2021.11-Linux-x86_64.sh -O ~/anaconda.sh \
    && bash ~/anaconda.sh -b -p /opt/conda \
    && rm ~/anaconda.sh
ENV PATH="/opt/conda/bin:${PATH}"
RUN conda init bash
RUN conda create -n genomel_editor python=3.11

# Install git
RUN apt update && apt install -y git

# Install all requirements
COPY ./requirements.txt .
RUN /bin/bash -c "source activate genomel_editor && pip install -r requirements.txt"

# Copy all project files to the VM
COPY ./data /opt/genomel_editor/data
COPY ./genomel_editor /opt/genomel_editor/genomel_editor
COPY ./GenomelEditor /opt/genomel_editor/GenomelEditor
COPY ./templates /opt/genomel_editor/templates
COPY ./manage.py /opt/genomel_editor/manage.py

# Change the working directory
WORKDIR /opt/genomel_editor

# Create the entrypoint script file and add the content
RUN echo '#!/bin/bash\n' \
    '# Script that supervisor uses to keep the genomel_editor running.\n' \
    '. ~/.bashrc\n' \
    'if ! ps ax | grep -v grep | grep "genomel_editor/bin/gunicorn genomel_editor.wsgi:application --bind 0.0.0.0:7999" > /dev/null\n' \
    'then\n' \
    '    # Log restart\n' \
    '    echo "Genomel Editor down; restarting run_genomel_editor.sh"\n' \
    '    # The right conda environment\n' \
    '    conda activate genomel_editor\n' \
    '    # Apply database migrations without prompting for user input\n' \
    '    python manage.py migrate --no-input\n' \
    '    # Collect static files from your various applications into one location\n' \
    '    python manage.py collectstatic --no-input\n' \
    "    # Create superuser admin account to be able to log into the Django project's admin page\n" \
    '    DJANGO_SUPERUSER_PASSWORD=$SUPER_USER_PASSWORD python manage.py createsuperuser --username $SUPER_USER_NAME --email $SUPER_USER_EMAIL --noinput\n' \
    '    # Run the Django application using gunicorn\n' \
    '    gunicorn genomel_editor.wsgi:application --bind 0.0.0.0:7999\n' \
    'fi\n' \
    | sed 's/^ //g' \
    > /opt/run_genomel_editor.sh
RUN chmod +x /opt/run_genomel_editor.sh


# Install Supervisord
RUN apt-get update && apt-get install -y supervisor \
&& rm -rf /var/lib/apt/lists/*
RUN echo '[program:genomel_editor]\n' \
    'command=/opt/run_genomel_editor.sh\n' \
    'autostart=true\n' \
    'autorestart=true\n' \
    'stderr_logfile=/var/log/run_genomel_editor.err.log\n' \
    'stdout_logfile=/var/log/run_genomel_editor.out.log\n' \
    | sed 's/^ //g' \
    > "/etc/supervisor/conf.d/supervisord.conf"

# Set default ENV variables if not set yet (for instance in docker compose)
ENV SUPER_USER_NAME="root"
ENV SUPER_USER_PASSWORD="root"
ENV SUPER_USER_EMAIL="root@root.com"

# Expose port 7999
EXPOSE 7999

CMD ["/usr/bin/supervisord","-n", "-c", "/etc/supervisor/supervisord.conf"]