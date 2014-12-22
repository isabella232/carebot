#!/usr/bin/env python

from datetime import datetime
import subprocess

from django.db import models
import yaml

import app_config
import flat

class Query(models.Model):
    slug = models.SlugField(max_length=128, unique=True)
    name = models.CharField(max_length=128)
    clan_yaml = models.TextField()

    def __unicode__(self):
       return self.name 

class Project(models.Model):
    slug = models.SlugField(max_length=128, unique=True)
    title = models.CharField(max_length=128)
    property_id = models.CharField(max_length=10, default='53470309')
    domain = models.CharField(max_length=128, default='apps.npr.org')
    prefix = models.CharField(max_length=128)
    start_date = models.DateField()
    queries = models.ManyToManyField(Query, through='ProjectQuery')

    class Meta:
        ordering = ('start_date',)

    def __unicode__(self):
        return self.title

    def build_clan_yaml(self):
        data = { }

        if self.title:
            data['title'] = self.title

        if self.property_id:
            data['property-id'] = self.property_id
        
        if self.domain:
            data['domain'] = self.domain
        
        if self.prefix:
            data['prefix'] = self.prefix
        
        if self.start_date:
            data['start-date'] = datetime.strftime(self.start_date, '%Y-%m-%d')
        
        if self.queries:
            data['queries'] = []

        for query in self.queries.all():
            y = yaml.load(query.clan_yaml)

            data['queries'].append(y)

        return yaml.safe_dump(data, encoding='utf-8', allow_unicode=True)

    def run_report(self, s3=None):
        with open('/tmp/clan.yaml', 'w') as f:
            y = self.build_clan_yaml()
            f.write(y)

        subprocess.call(['clan', 'report', '/tmp/clan.yaml', '/tmp/clan.html'])

        if not s3:
            import boto

            s3 = boto.connect_s3()

        flat.deploy_file(
            s3,
            '/tmp/clan.html',
            '%s/reports/%s/index.html' % (app_config.PROJECT_SLUG, self.slug),
            app_config.DEFAULT_MAX_AGE
        )

class ProjectQuery(models.Model):
    project = models.ForeignKey(Project)
    query = models.ForeignKey(Query)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ('order',)
