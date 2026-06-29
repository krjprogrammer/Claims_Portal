from django.db import models
from django.contrib.auth.models import AbstractUser

class Transaction(models.Model):
    filename = models.CharField(max_length=500)
    filetype = models.CharField(max_length=1)
    claim_count = models.IntegerField()
    created_date = models.DateField()

    def __str__(self):
        return self.filename
    

class EDICLHP(models.Model):

    BHPNAM = models.CharField(max_length=255, null=True, blank=True)
    BHNPI = models.CharField(max_length=255, null=True, blank=True)
    BHTXID = models.CharField(max_length=255, null=True, blank=True)
    BHPAD1 = models.CharField(max_length=255, null=True, blank=True)
    BHPCTY = models.CharField(max_length=255, null=True, blank=True)
    BHPST = models.CharField(max_length=255, null=True, blank=True)
    BHPZIP = models.CharField(max_length=255, null=True, blank=True)
    BHCFID = models.CharField(max_length=255, null=True, blank=True)
    BHGRPN = models.CharField(max_length=255, null=True, blank=True)
    BHGRNM = models.CharField(max_length=255, null=True, blank=True)
    BHMFNM = models.CharField(max_length=255, null=True, blank=True)
    BHMLNM = models.CharField(max_length=255, null=True, blank=True)
    BHMINT = models.CharField(max_length=255, null=True, blank=True)
    BHMAD1 = models.CharField(max_length=255, null=True, blank=True)
    BHMCTY = models.CharField(max_length=255, null=True, blank=True)
    BHMST = models.CharField(max_length=255, null=True, blank=True)
    BHMZIP = models.CharField(max_length=255, null=True, blank=True)
    BHMBDT = models.CharField(max_length=255, null=True, blank=True)
    BHMSEX = models.CharField(max_length=255, null=True, blank=True)
    BHMID = models.CharField(max_length=255, null=True, blank=True)
    BHORGN = models.CharField(max_length=255, null=True, blank=True)
    BHCHGA = models.CharField(max_length=255, null=True, blank=True)
    BHPLSR = models.CharField(max_length=255, null=True, blank=True)
    BHFREQ = models.CharField(max_length=255, null=True, blank=True)
    BHACPA = models.CharField(max_length=255, null=True, blank=True)
    BHDASG = models.CharField(max_length=255, null=True, blank=True)
    BHRELI = models.CharField(max_length=255, null=True, blank=True)
    BHDMRE = models.CharField(max_length=255, null=True, blank=True)
    BHRECD = models.CharField(max_length=255, null=True, blank=True)
    BHBFRD = models.CharField(max_length=255, null=True, blank=True)
    BHBTOD = models.CharField(max_length=255, null=True, blank=True)
    BHLDWK = models.CharField(max_length=255, null=True, blank=True)
    BHDOCN = models.CharField(max_length=255, null=True, blank=True)
    BHADJR = models.CharField(max_length=255, null=True, blank=True)
    BHNOTC = models.CharField(max_length=255, null=True, blank=True)
    BHNOTE = models.TextField(null=True, blank=True)
    BHDIO1 = models.CharField(max_length=255, null=True, blank=True)
    BHCAMT = models.CharField(max_length=255, null=True, blank=True)
    BHPPOI = models.CharField(max_length=255, null=True, blank=True)
    BHREV = models.CharField(max_length=255, null=True, blank=True)
    BHSNAM = models.CharField(max_length=255, null=True, blank=True)
    BHSAD1 = models.CharField(max_length=255, null=True, blank=True)
    BHSCTY = models.CharField(max_length=255, null=True, blank=True)
    BHSST = models.CharField(max_length=255, null=True, blank=True)
    BHSZIP = models.CharField(max_length=255, null=True, blank=True)
    BHDFNM = models.CharField(max_length=255, null=True, blank=True)
    BHDLNM = models.CharField(max_length=255, null=True, blank=True)
    BHDINT = models.CharField(max_length=255, null=True, blank=True)
    BHDAD1 = models.CharField(max_length=255, null=True, blank=True)
    BHDCTY = models.CharField(max_length=255, null=True, blank=True)
    BHDST = models.CharField(max_length=255, null=True, blank=True)
    BHDZIP = models.CharField(max_length=255, null=True, blank=True)
    BHDBDT = models.CharField(max_length=255, null=True, blank=True)
    BHDSEX = models.CharField(max_length=255, null=True, blank=True)
    BHDIO2 = models.CharField(max_length=255, null=True, blank=True)
    BHPHNM = models.CharField(max_length=255, null=True, blank=True)
    BHPHID = models.CharField(max_length=255, null=True, blank=True)
    BHTAXO = models.CharField(max_length=255, null=True, blank=True)
    BHDIO3 = models.CharField(max_length=255, null=True, blank=True)
    BHDIO4 = models.CharField(max_length=255, null=True, blank=True)
    BHDIO5 = models.CharField(max_length=255, null=True, blank=True)
    BHOICO = models.CharField(max_length=255, null=True, blank=True)
    BHOIDE = models.CharField(max_length=255, null=True, blank=True)
    BHNPA1 = models.CharField(max_length=255, null=True, blank=True)
    BHOPPA = models.CharField(max_length=255, null=True, blank=True)
    BHMEDA = models.CharField(max_length=255, null=True, blank=True)
    BHCALA = models.CharField(max_length=255, null=True, blank=True)
    BHOICP = models.CharField(max_length=255, null=True, blank=True)
    BHNPR2 = models.CharField(max_length=255, null=True, blank=True)
    BHNPA2 = models.CharField(max_length=255, null=True, blank=True)
    BHNOTE2 = models.TextField(null=True, blank=True)
    BHCCBT = models.CharField(max_length=255, null=True, blank=True)
    BHCNTN = models.CharField(max_length=255, null=True, blank=True)
    BHSNDI = models.CharField(max_length=255, null=True, blank=True)
    BHPAYC = models.CharField(max_length=255, null=True, blank=True)
    BHPARN = models.CharField(max_length=255, null=True, blank=True)
    BHRCVI = models.CharField(max_length=255, null=True, blank=True)
    BHAMDG = models.CharField(max_length=255, null=True, blank=True)
    BHSNPI = models.CharField(max_length=255, null=True, blank=True)
    BHCNCD = models.CharField(max_length=255, null=True, blank=True)
    BHOIAL = models.CharField(max_length=255, null=True, blank=True)
    mem_dob = models.CharField(max_length=255, null=True, blank=True)
    dep_dob = models.CharField(max_length=255, null=True, blank=True)
    BHSQCL = models.CharField(max_length=255, null=True, blank=True)
    TEDSSN = models.CharField(max_length=255, null=True, blank=True)
    BHCLNT = models.CharField(max_length=255, null=True, blank=True)
    BHPSEQ = models.CharField(max_length=255, null=True, blank=True)
    BHMEMN = models.CharField(max_length=255, null=True, blank=True)
    BHRLTN = models.CharField(max_length=255, null=True, blank=True)
    BHDREL = models.CharField(max_length=255, null=True, blank=True)
    BHDEPN = models.CharField(max_length=255, null=True, blank=True)
    BHDCNT = models.CharField(max_length=255, null=True, blank=True)
    BHREFC = models.CharField(max_length=255, null=True, blank=True)
    BHTXSN = models.CharField(max_length=255, null=True, blank=True)
    BHCLTP = models.CharField(max_length=255, null=True, blank=True)
    BHMVRF = models.CharField(max_length=10, null=True, blank=True)
    BHPRVRF = models.CharField(max_length=10, null=True, blank=True)
    BHPBSEQ = models.CharField(max_length=10, null=True, blank=True)
    filename = models.CharField(max_length=100,null=True,blank=True)
    class Meta:
        db_table = "ediclhp"


class Fund_Data(models.Model):
    FUND = models.CharField(max_length=255, null=True, blank=True)
    CLAIMS = models.CharField(max_length=255, null=True, blank=True)
    claim_amount = models.CharField(max_length=255, null=True, blank=True)
    allowed_amount = models.CharField(max_length=255, null=True, blank=True)
    paid_amount = models.CharField(max_length=255, null=True, blank=True)
    group_name = models.CharField(max_length=255, null=True, blank=True)
    group_count = models.CharField(max_length=255, null=True, blank=True)
    fund_type = models.CharField(max_length=255, null=True, blank=True)
    filename = models.CharField(max_length=255, null=True, blank=True)
    file_date = models.CharField(max_length=255, null=True, blank=True)
    class Meta:
        db_table = "fund_data"


class Fund_Status(models.Model):
    Fund = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    Groups = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    Status = models.CharField(
        max_length=1,
        null=True,
        blank=True
    )
    class Meta:
        db_table = "fund_status"



class Total_Charges(models.Model):

    total_claim_amount = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    total_allowed_amount = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    total_paid_amount = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    file_date = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    filetype = models.CharField(
        max_length=10,
        null=True,
        blank=True
    )

    class Meta:
        db_table = "total_charges"


class EDIEMP(models.Model):

    TECLNT = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    TESEQ = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    TESSN = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    TEDSSN = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    TENAME = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    TEDOB = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    TEALTI = models.CharField(
        max_length=255,
        null=True,
        blank=True
    ) 
    TEHCID = models.CharField(
        max_length=255,
        null=True,
        blank=True
    ) 
    TEHMID = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    class Meta:
        db_table = "ediemp"


class DEPNP(models.Model):

    DPDROP = models.CharField(max_length=255, null=True, blank=True)
    DPCLNT = models.CharField(max_length=255, null=True, blank=True)
    DPSSN = models.CharField(max_length=255, null=True, blank=True)
    DPSEQ = models.CharField(max_length=255, null=True, blank=True)
    DPNAME = models.CharField(max_length=255, null=True, blank=True)
    DPLNAM = models.CharField(max_length=255, null=True, blank=True)
    DPDOBY = models.CharField(max_length=255, null=True, blank=True)
    DPDOBM = models.CharField(max_length=255, null=True, blank=True)
    DPDOBD = models.CharField(max_length=255, null=True, blank=True)
    DPDODY = models.CharField(max_length=255, null=True, blank=True)
    DPDODM = models.CharField(max_length=255, null=True, blank=True)
    DPDODD = models.CharField(max_length=255, null=True, blank=True)
    DPDSSN = models.CharField(max_length=255, null=True, blank=True)
    DPSEX = models.CharField(max_length=255, null=True, blank=True)
    DPTYPE = models.CharField(max_length=255, null=True, blank=True)
    DPRLTN = models.CharField(max_length=255, null=True, blank=True)
    DPEFDY = models.CharField(max_length=255, null=True, blank=True)
    DPEFDM = models.CharField(max_length=255, null=True, blank=True)
    DPEFDD = models.CharField(max_length=255, null=True, blank=True)
    DPTDTY = models.CharField(max_length=255, null=True, blank=True)
    DPTDTM = models.CharField(max_length=255, null=True, blank=True)
    DPTDTD = models.CharField(max_length=255, null=True, blank=True)
    DPCOB = models.CharField(max_length=255, null=True, blank=True)
    DPPLAN = models.CharField(max_length=255, null=True, blank=True)
    DPCLAS = models.CharField(max_length=255, null=True, blank=True)
    DPSTAT = models.CharField(max_length=255, null=True, blank=True)
    DPALTP = models.CharField(max_length=255, null=True, blank=True)
    DPSELF = models.CharField(max_length=255, null=True, blank=True)
    DPMDFL = models.CharField(max_length=255, null=True, blank=True)
    DPMEFY = models.CharField(max_length=255, null=True, blank=True)
    DPMEFM = models.CharField(max_length=255, null=True, blank=True)
    DPMEFD = models.CharField(max_length=255, null=True, blank=True)
    DPMGYY = models.CharField(max_length=255, null=True, blank=True)
    DPMGMM = models.CharField(max_length=255, null=True, blank=True)
    DPMGDD = models.CharField(max_length=255, null=True, blank=True)
    DPDVYY = models.CharField(max_length=255, null=True, blank=True)
    DPDVMM = models.CharField(max_length=255, null=True, blank=True)
    DPDVDD = models.CharField(max_length=255, null=True, blank=True)
    DPBSFL = models.CharField(max_length=255, null=True, blank=True)
    DPDSFL = models.CharField(max_length=255, null=True, blank=True)
    DPMGFL = models.CharField(max_length=255, null=True, blank=True)
    DPDVFL = models.CharField(max_length=255, null=True, blank=True)
    DPCRYY = models.CharField(max_length=255, null=True, blank=True)
    DPCRMM = models.CharField(max_length=255, null=True, blank=True)
    DPCRDD = models.CharField(max_length=255, null=True, blank=True)
    DPUPYY = models.CharField(max_length=255, null=True, blank=True)
    DPUPMM = models.CharField(max_length=255, null=True, blank=True)
    DPUPDD = models.CharField(max_length=255, null=True, blank=True)
    DPUSER = models.CharField(max_length=255, null=True, blank=True)
    DPCBVY = models.CharField(max_length=255, null=True, blank=True)
    DPCBVM = models.CharField(max_length=255, null=True, blank=True)
    DPHICN = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "depnp"


class PROVP(models.Model):

    PRSEQ = models.CharField(
        db_column="PRSEQ#",
        max_length=255,
        null=True,
        blank=True
    )

    PRBSEQ = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    PRPNAM = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    PRADR1 = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    PRCITY = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    PRST = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    PRZIP5 = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    PRNUM = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    class Meta:
        db_table = "provp"


class ProcessingLog(models.Model):
    filename = models.CharField(max_length=500, null=True, blank=True)
    filetype = models.CharField(max_length=10, null=True, blank=True)
    file_date = models.CharField(max_length=20, null=True, blank=True)
    status = models.CharField(max_length=100, null=True, blank=True)
    created_time = models.TimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = "processing_log"


class PortalPages(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = 'PortalPages'

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.strip().lower()
        super().save(*args, **kwargs)


class PortalRoles(models.Model):
    name = models.CharField(max_length=255, unique=True)
    access_pages = models.ManyToManyField(PortalPages, blank=True)

    class Meta:
        db_table = 'PortalRoles'

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class PortalUser(AbstractUser):
    role = models.ForeignKey(PortalRoles, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.BooleanField(default=True)
    temp_password = models.CharField(max_length=10,null=True,blank=True)
    totp_secret = models.CharField(max_length=64, null=True, blank=True)
    totp_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Portal User"
        verbose_name_plural = "Portal Users"
        db_table = 'PortalUser'
        ordering = ['username']

    @property
    def is_superadmin(self):
        return self.is_superuser or (self.role is not None and self.role.name.lower() == 'superadmin')

    def __str__(self):
        return self.username


class EmailOTP(models.Model):
    user = models.OneToOneField(PortalUser, on_delete=models.CASCADE, related_name="email_otp")
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.email} - {self.otp}"
